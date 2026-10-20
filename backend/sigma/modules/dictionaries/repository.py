from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sigma.modules.dictionaries.domain import (
    BudgetArticle,
    Category,
)
from sigma.modules.dictionaries.models import BudgetArticleModel, CategoryModel


def _category_to_domain(model: CategoryModel) -> Category:
    return Category(id=model.id, name=model.name, is_archived=model.is_archived)


def _category_to_model(category: Category) -> CategoryModel:
    return CategoryModel(
        id=category.id,
        name=category.name,
        is_archived=category.is_archived,
        normalized_name=category.normalized_name,
    )


def _budget_article_to_domain(model: BudgetArticleModel) -> BudgetArticle:
    return BudgetArticle(
        id=model.id, name=model.name, is_archived=model.is_archived, category_id=model.category_id
    )


def _budget_article_to_model(budget_article: BudgetArticle) -> BudgetArticleModel:
    return BudgetArticleModel(
        id=budget_article.id,
        name=budget_article.name,
        is_archived=budget_article.is_archived,
        category_id=budget_article.category_id,
        normalized_name=budget_article.normalized_name,
    )


class CategoryRepository(Protocol):
    async def get(self, category_id: UUID) -> Category | None: ...

    async def add(self, category: Category) -> None: ...

    async def list(self, *, include_archived: bool = False) -> list[Category]: ...

    async def name_exists(
        self, normalized_name: str, *, exclude_id: UUID | None = None
    ) -> bool: ...

    async def save(self, category: Category) -> None: ...


class BudgetArticleRepository(Protocol):
    async def get(self, id: UUID) -> BudgetArticle | None: ...

    async def add(self, budget_article: BudgetArticle) -> None: ...

    async def list(self, *, include_archived: bool = False) -> list[BudgetArticle]: ...

    async def list_by_category(
        self,
        category_id: UUID,
        *,
        include_archived: bool = False,
    ) -> list[BudgetArticle]: ...

    async def name_exists(
        self,
        normalized_name: str,
        *,
        exclude_id: UUID | None = None,
    ) -> bool: ...

    async def save(self, budget_article: BudgetArticle) -> None: ...


class SqlAlchemyCategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, category_id: UUID) -> Category | None:
        model = await self._session.get(CategoryModel, category_id)
        if model is None:
            return None
        return _category_to_domain(model)

    async def add(self, category: Category) -> None:
        self._session.add(_category_to_model(category))

    async def list(self, *, include_archived: bool = False) -> list[Category]:
        statement = select(CategoryModel)
        if not include_archived:
            statement = statement.where(CategoryModel.is_archived.is_(False))

        statement = statement.order_by(CategoryModel.normalized_name, CategoryModel.id)
        models = (await self._session.scalars(statement)).all()
        return [_category_to_domain(model) for model in models]

    async def name_exists(self, normalized_name: str, *, exclude_id: UUID | None = None) -> bool:
        query = select(CategoryModel.id).where(CategoryModel.normalized_name == normalized_name)
        if exclude_id is not None:
            query = query.where(CategoryModel.id != exclude_id)

        statement = select(query.exists())
        return bool(await self._session.scalar(statement))

    async def save(self, category: Category) -> None:
        await self._session.merge(_category_to_model(category))


class SqlAlchemyBudgetArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> BudgetArticle | None:
        model = await self._session.get(BudgetArticleModel, id)
        if model is None:
            return None
        return _budget_article_to_domain(model)

    async def add(self, budget_article: BudgetArticle) -> None:
        model = _budget_article_to_model(budget_article)
        self._session.add(model)

    async def list(self, *, include_archived: bool = False) -> list[BudgetArticle]:
        statement = select(BudgetArticleModel)
        if not include_archived:
            statement = statement.where(BudgetArticleModel.is_archived.is_(False))
        statement = statement.order_by(BudgetArticleModel.normalized_name, BudgetArticleModel.id)
        models = (await self._session.scalars(statement)).all()
        return [_budget_article_to_domain(model) for model in models]

    async def list_by_category(
        self,
        category_id: UUID,
        *,
        include_archived: bool = False,
    ) -> list[BudgetArticle]:
        statement = select(BudgetArticleModel).where(BudgetArticleModel.category_id == category_id)
        if not include_archived:
            statement = statement.where(BudgetArticleModel.is_archived.is_(False))
        statement = statement.order_by(BudgetArticleModel.normalized_name, BudgetArticleModel.id)
        models = (await self._session.scalars(statement)).all()
        return [_budget_article_to_domain(model) for model in models]

    async def name_exists(
        self,
        normalized_name: str,
        *,
        exclude_id: UUID | None = None,
    ) -> bool:
        query = select(BudgetArticleModel.id).where(
            BudgetArticleModel.normalized_name == normalized_name
        )
        if exclude_id is not None:
            query = query.where(BudgetArticleModel.id != exclude_id)

        statement = select(query.exists())
        return bool(await self._session.scalar(statement))

    async def save(self, budget_article: BudgetArticle) -> None:
        model = _budget_article_to_model(budget_article)
        await self._session.merge(model)
