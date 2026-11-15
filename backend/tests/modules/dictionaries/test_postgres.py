"""Opt-in integration checks; only an empty sigma_test_* database is accepted."""

import asyncio
import os
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi import FastAPI
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy import Connection, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from sigma.main import create_app
from sigma.modules.dictionaries.models import (
    BudgetArticleModel,
    CategoryModel,
    CFOModel,
    DistributionRuleModel,
    MRPModel,
)
from sigma.shared.config import settings
from sigma.shared.db import Base, get_session

BACKEND = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.postgres


async def table_names(url: str) -> set[str]:
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            return set(await connection.run_sync(lambda conn: inspect(conn).get_table_names()))
    finally:
        await engine.dispose()


async def run_isolated(url: str, exercise: Callable[[AsyncSession], Awaitable[None]]) -> None:
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                async with AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                ) as session:
                    await exercise(session)
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()


async def seed_previous_schema(url: str) -> None:
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO budget_categories (id, name, normalized_name, is_archived) "
                    "VALUES (:id, :name, :normalized_name, false)"
                ),
                {
                    "id": uuid4(),
                    "name": "Migration fixture",
                    "normalized_name": "migration fixture",
                },
            )
    finally:
        await engine.dispose()


async def require_previous_data(url: str) -> None:
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            count = await connection.scalar(
                text(
                    "SELECT count(*) FROM budget_categories "
                    "WHERE normalized_name = 'migration fixture'"
                )
            )
            assert count == 1
    finally:
        await engine.dispose()


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    url = os.environ.get("SIGMA_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set SIGMA_TEST_DATABASE_URL to an empty PostgreSQL test database")
    parsed = make_url(url)
    if parsed.drivername != "postgresql+asyncpg" or not (parsed.database or "").startswith(
        "sigma_test_"
    ):
        pytest.fail("Integration tests require postgresql+asyncpg and a sigma_test_* database")
    if asyncio.run(table_names(url)) - {"alembic_version"}:
        pytest.fail("Integration tests refuse to migrate a nonempty database")

    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "migrations"))
    previous_url = settings.database_url
    settings.database_url = url
    try:
        command.upgrade(config, "a5cfcb331828")
        asyncio.run(seed_previous_schema(url))
        command.upgrade(config, "head")
        asyncio.run(require_previous_data(url))
        yield url
        command.downgrade(config, "a5cfcb331828")
        asyncio.run(require_previous_data(url))
        command.downgrade(config, "base")
        assert asyncio.run(table_names(url)) == {"alembic_version"}
        command.upgrade(config, "head")
        command.downgrade(config, "base")
    finally:
        settings.database_url = previous_url


def test_migrated_schema_matches_orm(postgres_url: str) -> None:
    def compare(connection: Connection) -> None:
        context = MigrationContext.configure(connection)
        assert compare_metadata(context, Base.metadata) == []
        assert set(inspect(connection).get_table_names()) == {
            "alembic_version",
            "budget_categories",
            "budget_articles",
            "cfo",
            "mrp",
            "organizations",
            "distribution_rules",
        }

    async def exercise(session: AsyncSession) -> None:
        connection = await session.connection()
        await connection.run_sync(compare)

    asyncio.run(run_isolated(postgres_url, exercise))


@pytest.mark.parametrize("constraint", ["unique_name", "foreign_key", "unique_rule_pair"])
def test_database_rejects_constraint_violations(postgres_url: str, constraint: str) -> None:
    async def exercise(session: AsyncSession) -> None:
        category_id, article_id, cfo_id, mrp_id = (uuid4() for _ in range(4))
        category = CategoryModel(
            id=category_id, name="Constraint category", normalized_name="constraint category"
        )
        session.add_all(
            [
                category,
                CFOModel(id=cfo_id, name="Test CFO", normalized_name="test cfo"),
                MRPModel(id=mrp_id, name="Test MRP", normalized_name="test mrp"),
            ]
        )
        await session.flush()
        session.add(
            BudgetArticleModel(
                id=article_id, name="Article", normalized_name="article", category_id=category_id
            )
        )
        await session.flush()
        session.add(
            DistributionRuleModel(
                id=uuid4(), cfo_id=cfo_id, budget_article_id=article_id, mrp_id=mrp_id
            )
        )
        await session.flush()
        with pytest.raises(IntegrityError):
            async with session.begin_nested():
                if constraint == "unique_name":
                    session.add(
                        CategoryModel(
                            id=uuid4(), name="Duplicate", normalized_name="constraint category"
                        )
                    )
                else:
                    session.add(
                        DistributionRuleModel(
                            id=uuid4(),
                            cfo_id=cfo_id,
                            mrp_id=mrp_id,
                            budget_article_id=uuid4()
                            if constraint == "foreign_key"
                            else article_id,
                        )
                    )
                await session.flush()

    asyncio.run(run_isolated(postgres_url, exercise))


def create_test_app(session: AsyncSession) -> FastAPI:
    app = create_app()

    async def test_session() -> AsyncIterator[AsyncSession]:
        async with AsyncSession(
            bind=session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
        ) as request_session:
            yield request_session

    app.dependency_overrides[get_session] = test_session
    return app


def test_http_to_postgres_distribution_and_archiving(postgres_url: str) -> None:
    async def exercise(session: AsyncSession) -> None:
        transport = ASGITransport(app=create_test_app(session))
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            category = await client.post("/dictionaries/categories", json={"name": "HTTP category"})
            assert category.status_code == 201
            article = await client.post(
                "/dictionaries/articles",
                json={"name": "HTTP article", "category_id": category.json()["id"]},
            )
            assert article.status_code == 201
            cfo = await client.post("/dictionaries/cfos", json={"name": "HTTP CFO"})
            mrp = await client.post("/dictionaries/mrps", json={"name": "Test recipient"})
            assert cfo.status_code == mrp.status_code == 201
            pair = {"cfo_id": cfo.json()["id"], "budget_article_id": article.json()["id"]}
            rule = await client.post(
                "/dictionaries/savings-distribution-rules", json=pair | {"mrp_id": mrp.json()["id"]}
            )
            assert rule.status_code == 201
            listing = await client.get("/dictionaries/savings-distribution-rules")
            assert listing.status_code == 200
            assert listing.json()[0]["rule"]["id"] == rule.json()["id"]
            recommendation = await client.get(
                "/dictionaries/savings-distribution-rules/recommendation", params=pair
            )
            assert recommendation.status_code == 200
            assert recommendation.json()["id"] == mrp.json()["id"]
            archived = await client.post(
                f"/dictionaries/categories/{category.json()['id']}/archive"
            )
            assert archived.status_code == 200
            articles = await client.get("/dictionaries/articles")
            assert articles.status_code == 200
            assert articles.json() == []
            recommendation = await client.get(
                "/dictionaries/savings-distribution-rules/recommendation", params=pair
            )
            assert recommendation.status_code == 200
            assert recommendation.json() is None

    asyncio.run(run_isolated(postgres_url, exercise))


def test_http_to_postgres_organization_names_and_archive(postgres_url: str) -> None:
    async def exercise(session: AsyncSession) -> None:
        transport = ASGITransport(app=create_test_app(session))
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/dictionaries/organizations",
                json={"name": "  Test   organization  ", "external_name": 'LLC "Example"'},
            )
            assert created.status_code == 201
            assert created.json()["name"] == "Test organization"
            duplicate = await client.post(
                "/dictionaries/organizations",
                json={"name": "Other organization", "external_name": "LLC «Example»"},
            )
            assert duplicate.status_code == 409
            path = f"/dictionaries/organizations/{created.json()['id']}"
            renamed = await client.put(
                path, json={"name": "Renamed organization", "external_name": "Example renamed"}
            )
            assert renamed.status_code == 200
            assert renamed.json()["external_name"] == "Example renamed"
            archived = await client.post(f"{path}/archive")
            assert archived.status_code == 200
            listing = await client.get("/dictionaries/organizations")
            assert listing.status_code == 200
            assert listing.json() == []
            restored = await client.post(f"{path}/restore")
            assert restored.status_code == 200
            listing = await client.get("/dictionaries/organizations")
            assert listing.status_code == 200
            assert listing.json() == [restored.json()]

    asyncio.run(run_isolated(postgres_url, exercise))
