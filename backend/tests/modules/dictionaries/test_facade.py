import asyncio
from collections.abc import Mapping
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sigma.modules.dictionaries import facade as facade_module
from sigma.modules.dictionaries.domain import MRP, BudgetArticle, Category
from sigma.modules.dictionaries.facade import (
    DictionariesFacade,
    DuplicateDictionaryNameError,
    MRPNotFoundError,
)
from sigma.modules.dictionaries.repository import (
    SqlAlchemyBudgetArticleRepository,
    SqlAlchemyCategoryRepository,
    SqlAlchemyMRPRepository,
)


class _UniqueNameViolation(UniqueViolationError):
    constraint_name = "uq_mrp_normalized_name"


def _session_with_transaction() -> tuple[MagicMock, MagicMock]:
    session = MagicMock(spec=AsyncSession)
    transaction = MagicMock()
    transaction.__aenter__ = AsyncMock()
    transaction.__aexit__ = AsyncMock(return_value=False)
    session.begin.return_value = transaction
    return session, transaction


def _assert_successful_transaction(session: MagicMock, transaction: MagicMock) -> None:
    session.begin.assert_called_once_with()
    transaction.__aenter__.assert_awaited_once_with()
    transaction.__aexit__.assert_awaited_once_with(None, None, None)


def _awaited_call(mock: AsyncMock) -> tuple[tuple[object, ...], Mapping[str, object]]:
    awaited_call = mock.await_args
    assert awaited_call is not None
    return awaited_call.args, awaited_call.kwargs


def test_facade_exports_public_errors_without_domain_entities() -> None:
    assert set(facade_module.__all__) == {
        "ArchivedCategoryError",
        "ArticleCategoryMismatchError",
        "BudgetArticleNotFoundError",
        "CategoryNotFoundError",
        "DictionariesDomainError",
        "DictionariesFacade",
        "DictionariesFeatureError",
        "DuplicateDictionaryNameError",
        "InvalidDictionaryNameError",
        "MRPNotFoundError",
    }


def test_facade_builds_repositories_with_same_session() -> None:
    session = MagicMock(spec=AsyncSession)

    with (
        patch(
            "sigma.modules.dictionaries.facade.SqlAlchemyCategoryRepository"
        ) as category_repository,
        patch(
            "sigma.modules.dictionaries.facade.SqlAlchemyBudgetArticleRepository"
        ) as article_repository,
        patch("sigma.modules.dictionaries.facade.SqlAlchemyMRPRepository") as mrp_repository,
    ):
        DictionariesFacade(session)

    category_repository.assert_called_once_with(session)
    article_repository.assert_called_once_with(session)
    mrp_repository.assert_called_once_with(session)


def test_create_category_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    category = Category(name="Транспорт")
    feature = AsyncMock(return_value=category)

    with patch("sigma.modules.dictionaries.facade.create_category_feature", feature):
        result = asyncio.run(DictionariesFacade(session).create_category("Транспорт"))

    assert result is category
    (name, repository), _ = _awaited_call(feature)
    assert name == "Транспорт"
    assert isinstance(repository, SqlAlchemyCategoryRepository)
    _assert_successful_transaction(session, transaction)


def test_rename_category_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    category = Category(name="Командировки")
    feature = AsyncMock(return_value=category)

    with patch("sigma.modules.dictionaries.facade.rename_category_feature", feature):
        result = asyncio.run(
            DictionariesFacade(session).rename_category(category.id, "Командировки")
        )

    assert result is category
    (category_id, new_name, repository), _ = _awaited_call(feature)
    assert category_id == category.id
    assert new_name == "Командировки"
    assert isinstance(repository, SqlAlchemyCategoryRepository)
    _assert_successful_transaction(session, transaction)


def test_restore_category_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    category = Category(name="Транспорт")
    feature = AsyncMock(return_value=category)

    with patch("sigma.modules.dictionaries.facade.restore_category_feature", feature):
        result = asyncio.run(DictionariesFacade(session).restore_category(category.id))

    assert result is category
    (category_id, repository), _ = _awaited_call(feature)
    assert category_id == category.id
    assert isinstance(repository, SqlAlchemyCategoryRepository)
    _assert_successful_transaction(session, transaction)


def test_archive_category_passes_both_repositories() -> None:
    session, transaction = _session_with_transaction()
    category = Category(name="Транспорт", is_archived=True)
    feature = AsyncMock(return_value=category)

    with patch("sigma.modules.dictionaries.facade.archive_category_feature", feature):
        result = asyncio.run(DictionariesFacade(session).archive_category(category.id))

    assert result is category
    (category_id, category_repository, article_repository), _ = _awaited_call(feature)
    assert category_id == category.id
    assert isinstance(category_repository, SqlAlchemyCategoryRepository)
    assert isinstance(article_repository, SqlAlchemyBudgetArticleRepository)
    _assert_successful_transaction(session, transaction)


def test_list_categories_passes_filter_without_write_transaction() -> None:
    session = MagicMock(spec=AsyncSession)
    categories = [Category(name="Транспорт")]
    feature = AsyncMock(return_value=categories)

    with patch("sigma.modules.dictionaries.facade.list_categories_feature", feature):
        result = asyncio.run(DictionariesFacade(session).list_categories(include_archived=True))

    assert result == categories
    feature.assert_awaited_once()
    (repository,), kwargs = _awaited_call(feature)
    assert isinstance(repository, SqlAlchemyCategoryRepository)
    assert kwargs == {"include_archived": True}
    session.begin.assert_not_called()


def test_create_article_passes_both_repositories() -> None:
    session, transaction = _session_with_transaction()
    category = Category(name="Транспорт")
    article = BudgetArticle.create("Ремонт", category)
    feature = AsyncMock(return_value=article)

    with patch("sigma.modules.dictionaries.facade.create_article_feature", feature):
        result = asyncio.run(DictionariesFacade(session).create_article("Ремонт", category.id))

    assert result is article
    (name, category_id, category_repository, article_repository), _ = _awaited_call(feature)
    assert name == "Ремонт"
    assert category_id == category.id
    assert isinstance(category_repository, SqlAlchemyCategoryRepository)
    assert isinstance(article_repository, SqlAlchemyBudgetArticleRepository)
    _assert_successful_transaction(session, transaction)


def test_rename_article_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    category = Category(name="Транспорт")
    article = BudgetArticle.create("Техосмотр", category)
    feature = AsyncMock(return_value=article)

    with patch("sigma.modules.dictionaries.facade.rename_article_feature", feature):
        result = asyncio.run(DictionariesFacade(session).rename_article(article.id, "Техосмотр"))

    assert result is article
    (article_id, new_name, repository), _ = _awaited_call(feature)
    assert article_id == article.id
    assert new_name == "Техосмотр"
    assert isinstance(repository, SqlAlchemyBudgetArticleRepository)
    _assert_successful_transaction(session, transaction)


def test_move_article_passes_both_repositories() -> None:
    session, transaction = _session_with_transaction()
    current_category = Category(name="Транспорт")
    target_category_id = uuid4()
    article = BudgetArticle.create("Ремонт", current_category)
    feature = AsyncMock(return_value=article)

    with patch("sigma.modules.dictionaries.facade.move_article_feature", feature):
        result = asyncio.run(
            DictionariesFacade(session).move_article(article.id, target_category_id)
        )

    assert result is article
    (article_id, passed_category_id, article_repository, category_repository), _ = _awaited_call(
        feature
    )
    assert article_id == article.id
    assert passed_category_id == target_category_id
    assert isinstance(article_repository, SqlAlchemyBudgetArticleRepository)
    assert isinstance(category_repository, SqlAlchemyCategoryRepository)
    _assert_successful_transaction(session, transaction)


def test_restore_article_passes_both_repositories() -> None:
    session, transaction = _session_with_transaction()
    category = Category(name="Транспорт")
    article = BudgetArticle.create("Ремонт", category)
    feature = AsyncMock(return_value=article)

    with patch("sigma.modules.dictionaries.facade.restore_article_feature", feature):
        result = asyncio.run(DictionariesFacade(session).restore_article(article.id))

    assert result is article
    (article_id, article_repository, category_repository), _ = _awaited_call(feature)
    assert article_id == article.id
    assert isinstance(article_repository, SqlAlchemyBudgetArticleRepository)
    assert isinstance(category_repository, SqlAlchemyCategoryRepository)
    _assert_successful_transaction(session, transaction)


def test_archive_article_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    category = Category(name="Транспорт")
    article = BudgetArticle.create("Ремонт", category)
    feature = AsyncMock(return_value=article)

    with patch("sigma.modules.dictionaries.facade.archive_article_feature", feature):
        result = asyncio.run(DictionariesFacade(session).archive_article(article.id))

    assert result is article
    (article_id, repository), _ = _awaited_call(feature)
    assert article_id == article.id
    assert isinstance(repository, SqlAlchemyBudgetArticleRepository)
    _assert_successful_transaction(session, transaction)


def test_list_articles_passes_filter_without_write_transaction() -> None:
    session = MagicMock(spec=AsyncSession)
    category = Category(name="Транспорт")
    articles = [BudgetArticle.create("Ремонт", category)]
    feature = AsyncMock(return_value=articles)

    with patch("sigma.modules.dictionaries.facade.list_articles_feature", feature):
        result = asyncio.run(DictionariesFacade(session).list_articles(include_archived=True))

    assert result == articles
    feature.assert_awaited_once()
    (repository,), kwargs = _awaited_call(feature)
    assert isinstance(repository, SqlAlchemyBudgetArticleRepository)
    assert kwargs == {"include_archived": True}
    session.begin.assert_not_called()


def test_facade_propagates_feature_error_through_transaction() -> None:
    session, transaction = _session_with_transaction()
    error = DuplicateDictionaryNameError("Транспорт")
    feature = AsyncMock(side_effect=error)

    with (
        patch("sigma.modules.dictionaries.facade.create_category_feature", feature),
        pytest.raises(DuplicateDictionaryNameError, match="Транспорт"),
    ):
        asyncio.run(DictionariesFacade(session).create_category("Транспорт"))

    session.begin.assert_called_once_with()
    transaction.__aenter__.assert_awaited_once_with()
    exit_args = transaction.__aexit__.await_args.args
    assert exit_args[0] is DuplicateDictionaryNameError
    assert exit_args[1] is error
    assert exit_args[2] is not None


def test_create_mrp_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    mrp = MRP(name="Иванов")
    feature = AsyncMock(return_value=mrp)

    with patch("sigma.modules.dictionaries.facade.create_mrp_feature", feature):
        result = asyncio.run(DictionariesFacade(session).create_mrp("Иванов"))

    assert result is mrp
    (name, repository), _ = _awaited_call(feature)
    assert name == "Иванов"
    assert isinstance(repository, SqlAlchemyMRPRepository)
    _assert_successful_transaction(session, transaction)


def test_rename_mrp_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    mrp = MRP(name="Петров")
    feature = AsyncMock(return_value=mrp)

    with patch("sigma.modules.dictionaries.facade.rename_mrp_feature", feature):
        result = asyncio.run(DictionariesFacade(session).rename_mrp(mrp.id, "Петров"))

    assert result is mrp
    (mrp_id, new_name, repository), _ = _awaited_call(feature)
    assert mrp_id == mrp.id
    assert new_name == "Петров"
    assert isinstance(repository, SqlAlchemyMRPRepository)
    _assert_successful_transaction(session, transaction)


def test_archive_mrp_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    mrp = MRP(name="Иванов", is_archived=True)
    feature = AsyncMock(return_value=mrp)

    with patch("sigma.modules.dictionaries.facade.archive_mrp_feature", feature):
        result = asyncio.run(DictionariesFacade(session).archive_mrp(mrp.id))

    assert result is mrp
    (mrp_id, repository), _ = _awaited_call(feature)
    assert mrp_id == mrp.id
    assert isinstance(repository, SqlAlchemyMRPRepository)
    _assert_successful_transaction(session, transaction)


def test_restore_mrp_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    mrp = MRP(name="Иванов")
    feature = AsyncMock(return_value=mrp)

    with patch("sigma.modules.dictionaries.facade.restore_mrp_feature", feature):
        result = asyncio.run(DictionariesFacade(session).restore_mrp(mrp.id))

    assert result is mrp
    (mrp_id, repository), _ = _awaited_call(feature)
    assert mrp_id == mrp.id
    assert isinstance(repository, SqlAlchemyMRPRepository)
    _assert_successful_transaction(session, transaction)


@pytest.mark.parametrize("include_archived", [False, True])
def test_list_mrps_passes_filter_without_write_transaction(include_archived: bool) -> None:
    session = MagicMock(spec=AsyncSession)
    mrps = [MRP(name="Иванов")]
    feature = AsyncMock(return_value=mrps)

    with patch("sigma.modules.dictionaries.facade.list_mrps_feature", feature):
        result = asyncio.run(
            DictionariesFacade(session).list_mrps(include_archived=include_archived)
        )

    assert result is mrps
    feature.assert_awaited_once()
    (repository,), kwargs = _awaited_call(feature)
    assert isinstance(repository, SqlAlchemyMRPRepository)
    assert kwargs == {"include_archived": include_archived}
    session.begin.assert_not_called()


def test_list_mrps_excludes_archived_by_default() -> None:
    session = MagicMock(spec=AsyncSession)
    feature = AsyncMock(return_value=[])

    with patch("sigma.modules.dictionaries.facade.list_mrps_feature", feature):
        assert asyncio.run(DictionariesFacade(session).list_mrps()) == []

    _, kwargs = _awaited_call(feature)
    assert kwargs == {"include_archived": False}
    session.begin.assert_not_called()


@pytest.mark.parametrize("rename", [False, True])
@pytest.mark.parametrize("on_commit", [False, True])
def test_mrp_name_conflict_propagates_unchanged(rename: bool, on_commit: bool) -> None:
    session, transaction = _session_with_transaction()
    driver_error = _UniqueNameViolation("duplicate name")
    adapter_error = Exception("adapter error")
    adapter_error.__cause__ = driver_error
    error = IntegrityError("statement", {}, adapter_error)
    feature = AsyncMock(return_value=MRP(name="Иванов"))
    if on_commit:
        transaction.__aexit__.side_effect = error
    else:
        feature.side_effect = error
    feature_name = "rename_mrp_feature" if rename else "create_mrp_feature"

    with (
        patch(f"sigma.modules.dictionaries.facade.{feature_name}", feature),
        pytest.raises(IntegrityError) as caught,
    ):
        facade = DictionariesFacade(session)
        if rename:
            asyncio.run(facade.rename_mrp(uuid4(), "Иванов"))
        else:
            asyncio.run(facade.create_mrp("Иванов"))

    assert caught.value is error
    transaction.__aexit__.assert_awaited_once()


@pytest.mark.parametrize("rename", [False, True])
@pytest.mark.parametrize("cause_kind", ["other_constraint", "non_unique", "no_cause"])
def test_mrp_writes_propagate_unrelated_integrity_errors(rename: bool, cause_kind: str) -> None:
    session, transaction = _session_with_transaction()
    adapter_error = Exception("adapter error")
    if cause_kind == "other_constraint":
        driver_error = _UniqueNameViolation("duplicate id")
        driver_error.constraint_name = "pk_mrp"
        adapter_error.__cause__ = driver_error
    elif cause_kind == "non_unique":
        adapter_error.__cause__ = ValueError("not a unique violation")
    error = IntegrityError("statement", {}, adapter_error)
    feature = AsyncMock(side_effect=error)
    feature_name = "rename_mrp_feature" if rename else "create_mrp_feature"

    with (
        patch(f"sigma.modules.dictionaries.facade.{feature_name}", feature),
        pytest.raises(IntegrityError) as caught,
    ):
        facade = DictionariesFacade(session)
        if rename:
            asyncio.run(facade.rename_mrp(uuid4(), "Иванов"))
        else:
            asyncio.run(facade.create_mrp("Иванов"))

    assert caught.value is error
    assert transaction.__aexit__.await_args.args[1] is error


def test_mrp_feature_error_propagates_through_transaction() -> None:
    session, transaction = _session_with_transaction()
    mrp_id = uuid4()
    error = MRPNotFoundError(mrp_id)
    feature = AsyncMock(side_effect=error)

    with (
        patch("sigma.modules.dictionaries.facade.archive_mrp_feature", feature),
        pytest.raises(MRPNotFoundError) as caught,
    ):
        asyncio.run(DictionariesFacade(session).archive_mrp(mrp_id))

    assert caught.value is error
    assert transaction.__aexit__.await_args.args[0] is MRPNotFoundError
    assert transaction.__aexit__.await_args.args[1] is error
