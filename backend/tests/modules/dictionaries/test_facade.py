import asyncio
from collections.abc import Mapping
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from sigma.modules.dictionaries import facade as facade_module
from sigma.modules.dictionaries.domain import BudgetArticle, Category
from sigma.modules.dictionaries.facade import (
    DictionariesFacade,
    DuplicateDictionaryNameError,
)
from sigma.modules.dictionaries.repository import (
    SqlAlchemyBudgetArticleRepository,
    SqlAlchemyCategoryRepository,
)


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
    ):
        DictionariesFacade(session)

    category_repository.assert_called_once_with(session)
    article_repository.assert_called_once_with(session)


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
