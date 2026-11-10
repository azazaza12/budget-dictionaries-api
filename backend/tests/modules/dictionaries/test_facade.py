import asyncio
from collections.abc import Mapping
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from asyncpg.exceptions import NotNullViolationError, UniqueViolationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sigma.modules.dictionaries import facade as facade_module
from sigma.modules.dictionaries.domain import CFO, MRP, BudgetArticle, Category, Organization
from sigma.modules.dictionaries.facade import (
    DictionariesFacade,
    DuplicateDictionaryNameError,
    DuplicateOrganizationNameIn1CError,
    MRPNotFoundError,
    OrganizationNotFoundError,
)
from sigma.modules.dictionaries.repository import (
    SqlAlchemyBudgetArticleRepository,
    SqlAlchemyCategoryRepository,
    SqlAlchemyCFORepository,
    SqlAlchemyMRPRepository,
    SqlAlchemyOrganizationRepository,
)


class _UniqueNameViolation(UniqueViolationError):
    constraint_name = "uq_mrp_normalized_name"


class _UniqueViolation(UniqueViolationError):
    constraint_name = "uq_cfo_normalized_name"


class _PrimaryKeyViolation(UniqueViolationError):
    constraint_name = "pk_cfo"


class _NotNullViolation(NotNullViolationError):
    constraint_name = "uq_cfo_normalized_name"


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
        "CFONotFoundError",
        "DictionariesDomainError",
        "DictionariesFacade",
        "DictionariesFeatureError",
        "DuplicateDictionaryNameError",
        "DuplicateOrganizationNameIn1CError",
        "InvalidDictionaryNameError",
        "MRPNotFoundError",
        "OrganizationNotFoundError",
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
        patch("sigma.modules.dictionaries.facade.SqlAlchemyCFORepository") as cfo_repository,
        patch(
            "sigma.modules.dictionaries.facade.SqlAlchemyOrganizationRepository"
        ) as organization_repository,
    ):
        DictionariesFacade(session)

    category_repository.assert_called_once_with(session)
    article_repository.assert_called_once_with(session)
    mrp_repository.assert_called_once_with(session)
    cfo_repository.assert_called_once_with(session)
    organization_repository.assert_called_once_with(session)


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


def test_create_cfo_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    cfo = CFO(name="Закупки")
    feature = AsyncMock(return_value=cfo)

    with patch("sigma.modules.dictionaries.facade.create_cfo_feature", feature):
        result = asyncio.run(DictionariesFacade(session).create_cfo("Закупки"))

    assert result is cfo
    (name, repository), _ = _awaited_call(feature)
    assert name == "Закупки"
    assert isinstance(repository, SqlAlchemyCFORepository)
    _assert_successful_transaction(session, transaction)


def test_rename_cfo_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    cfo = CFO(name="Снабжение")
    feature = AsyncMock(return_value=cfo)

    with patch("sigma.modules.dictionaries.facade.rename_cfo_feature", feature):
        result = asyncio.run(DictionariesFacade(session).rename_cfo(cfo.id, "Снабжение"))

    assert result is cfo
    (cfo_id, name, repository), _ = _awaited_call(feature)
    assert cfo_id == cfo.id
    assert name == "Снабжение"
    assert isinstance(repository, SqlAlchemyCFORepository)
    _assert_successful_transaction(session, transaction)


@pytest.mark.parametrize("restore", [False, True])
def test_cfo_archive_and_restore_run_in_transaction(restore: bool) -> None:
    session, transaction = _session_with_transaction()
    cfo = CFO(name="Закупки", is_archived=not restore)
    feature = AsyncMock(return_value=cfo)
    feature_name = "restore_cfo_feature" if restore else "archive_cfo_feature"

    with patch(f"sigma.modules.dictionaries.facade.{feature_name}", feature):
        facade = DictionariesFacade(session)
        result = asyncio.run(facade.restore_cfo(cfo.id) if restore else facade.archive_cfo(cfo.id))

    assert result is cfo
    (cfo_id, repository), _ = _awaited_call(feature)
    assert cfo_id == cfo.id
    assert isinstance(repository, SqlAlchemyCFORepository)
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


@pytest.mark.parametrize("include_archived", [False, True])
def test_list_cfos_passes_filter_without_write_transaction(include_archived: bool) -> None:
    session = MagicMock(spec=AsyncSession)
    cfos = [CFO(name="Закупки")]
    feature = AsyncMock(return_value=cfos)

    with patch("sigma.modules.dictionaries.facade.list_cfos_feature", feature):
        result = asyncio.run(
            DictionariesFacade(session).list_cfos(include_archived=include_archived)
        )

    assert result is cfos
    (repository,), kwargs = _awaited_call(feature)
    assert isinstance(repository, SqlAlchemyCFORepository)
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
@pytest.mark.parametrize("at_commit", [False, True])
def test_cfo_name_conflict_propagates_unchanged(rename: bool, at_commit: bool) -> None:
    session, transaction = _session_with_transaction()
    violation = _UniqueViolation("duplicate name")
    original = Exception("adapted asyncpg error")
    original.__cause__ = violation
    error = IntegrityError("statement", {}, original)
    cfo = CFO(name="Закупки")
    feature = AsyncMock(return_value=cfo)
    if at_commit:
        transaction.__aexit__.side_effect = error
    else:
        feature.side_effect = error
    feature_name = "rename_cfo_feature" if rename else "create_cfo_feature"

    with (
        patch(f"sigma.modules.dictionaries.facade.{feature_name}", feature),
        pytest.raises(IntegrityError) as caught,
    ):
        facade = DictionariesFacade(session)
        asyncio.run(
            facade.rename_cfo(cfo.id, "Закупки") if rename else facade.create_cfo("Закупки")
        )

    assert caught.value is error
    transaction.__aexit__.assert_awaited_once()
    exit_args = transaction.__aexit__.await_args.args
    if at_commit:
        assert exit_args == (None, None, None)
    else:
        assert exit_args[0] is IntegrityError
        assert exit_args[1] is error


@pytest.mark.parametrize("rename", [False, True])
@pytest.mark.parametrize(
    "driver_error_type",
    [
        _PrimaryKeyViolation,
        _NotNullViolation,
        Exception,
    ],
)
def test_cfo_preserves_unrelated_integrity_errors(
    rename: bool,
    driver_error_type: type[Exception],
) -> None:
    session, transaction = _session_with_transaction()
    driver_error = driver_error_type("unrelated error")
    original = Exception("adapted asyncpg error")
    original.__cause__ = driver_error
    error = IntegrityError("statement", {}, original)
    feature = AsyncMock(side_effect=error)
    feature_name = "rename_cfo_feature" if rename else "create_cfo_feature"

    with (
        patch(f"sigma.modules.dictionaries.facade.{feature_name}", feature),
        pytest.raises(IntegrityError) as caught,
    ):
        facade = DictionariesFacade(session)
        asyncio.run(
            facade.rename_cfo(uuid4(), "Закупки") if rename else facade.create_cfo("Закупки")
        )

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


def test_cfo_feature_error_exits_transaction_unchanged() -> None:
    session, transaction = _session_with_transaction()
    error = facade_module.CFONotFoundError(uuid4())
    feature = AsyncMock(side_effect=error)

    with (
        patch("sigma.modules.dictionaries.facade.rename_cfo_feature", feature),
        pytest.raises(facade_module.CFONotFoundError) as caught,
    ):
        asyncio.run(DictionariesFacade(session).rename_cfo(error.cfo_id, "Закупки"))

    assert caught.value is error
    exit_args = transaction.__aexit__.await_args.args
    assert exit_args[0] is facade_module.CFONotFoundError
    assert exit_args[1] is error


def test_create_organization_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    organization = Organization(name="Пример", name_in_1c="ООО «Тестовая Компания»")
    feature = AsyncMock(return_value=organization)

    with patch("sigma.modules.dictionaries.facade.create_organization_feature", feature):
        result = asyncio.run(
            DictionariesFacade(session).create_organization(
                organization.name, organization.name_in_1c
            )
        )

    assert result is organization
    feature.assert_awaited_once()
    (name, name_in_1c, repository), _ = _awaited_call(feature)
    assert name == organization.name
    assert name_in_1c == organization.name_in_1c
    assert isinstance(repository, SqlAlchemyOrganizationRepository)
    _assert_successful_transaction(session, transaction)


def test_rename_organization_runs_feature_in_transaction() -> None:
    session, transaction = _session_with_transaction()
    organization = Organization(name="Пример", name_in_1c="ООО «Тестовая Компания»")
    feature = AsyncMock(return_value=organization)

    with patch("sigma.modules.dictionaries.facade.rename_organization_feature", feature):
        result = asyncio.run(
            DictionariesFacade(session).rename_organization(
                organization.id, organization.name, organization.name_in_1c
            )
        )

    assert result is organization
    feature.assert_awaited_once()
    (organization_id, name, name_in_1c, repository), _ = _awaited_call(feature)
    assert organization_id == organization.id
    assert name == organization.name
    assert name_in_1c == organization.name_in_1c
    assert isinstance(repository, SqlAlchemyOrganizationRepository)
    _assert_successful_transaction(session, transaction)


@pytest.mark.parametrize(
    "error",
    [
        OrganizationNotFoundError(uuid4()),
        DuplicateDictionaryNameError("Пример"),
        DuplicateOrganizationNameIn1CError("ООО «Пример»"),
        facade_module.InvalidDictionaryNameError("Empty name"),
    ],
)
def test_rename_organization_error_exits_transaction_unchanged(error: Exception) -> None:
    session, transaction = _session_with_transaction()
    feature = AsyncMock(side_effect=error)

    with (
        patch("sigma.modules.dictionaries.facade.rename_organization_feature", feature),
        pytest.raises(type(error)) as caught,
    ):
        asyncio.run(DictionariesFacade(session).rename_organization(uuid4(), "Пример", "ООО «Пример»"))

    assert caught.value is error
    feature.assert_awaited_once()
    session.begin.assert_called_once_with()
    transaction.__aenter__.assert_awaited_once_with()
    transaction.__aexit__.assert_awaited_once()
    exit_args = transaction.__aexit__.await_args.args
    assert exit_args[0] is type(error)
    assert exit_args[1] is error
    assert exit_args[2] is not None


@pytest.mark.parametrize("restore", [False, True])
def test_organization_archive_and_restore_run_in_transaction(restore: bool) -> None:
    session, transaction = _session_with_transaction()
    organization = Organization(
        name="Пример", name_in_1c="ООО «Тестовая Компания»", is_archived=not restore
    )
    feature = AsyncMock(return_value=organization)
    feature_name = "restore_organization_feature" if restore else "archive_organization_feature"

    with patch(f"sigma.modules.dictionaries.facade.{feature_name}", feature):
        facade = DictionariesFacade(session)
        result = asyncio.run(
            facade.restore_organization(organization.id)
            if restore
            else facade.archive_organization(organization.id)
        )

    assert result is organization
    feature.assert_awaited_once()
    (organization_id, repository), _ = _awaited_call(feature)
    assert organization_id == organization.id
    assert isinstance(repository, SqlAlchemyOrganizationRepository)
    _assert_successful_transaction(session, transaction)


@pytest.mark.parametrize("include_archived", [False, True])
def test_list_organizations_passes_filter_without_write_transaction(include_archived: bool) -> None:
    session = MagicMock(spec=AsyncSession)
    organizations = [Organization(name="Пример", name_in_1c="ООО «Тестовая Компания»")]
    feature = AsyncMock(return_value=organizations)

    with patch("sigma.modules.dictionaries.facade.list_organizations_feature", feature):
        result = asyncio.run(
            DictionariesFacade(session).list_organizations(include_archived=include_archived)
        )

    assert result is organizations
    feature.assert_awaited_once()
    (repository,), kwargs = _awaited_call(feature)
    assert isinstance(repository, SqlAlchemyOrganizationRepository)
    assert kwargs == {"include_archived": include_archived}
    session.begin.assert_not_called()


def test_list_organizations_excludes_archived_by_default() -> None:
    session = MagicMock(spec=AsyncSession)
    feature = AsyncMock(return_value=[])

    with patch("sigma.modules.dictionaries.facade.list_organizations_feature", feature):
        assert asyncio.run(DictionariesFacade(session).list_organizations()) == []

    feature.assert_awaited_once()
    _, kwargs = _awaited_call(feature)
    assert kwargs == {"include_archived": False}
    session.begin.assert_not_called()


@pytest.mark.parametrize(
    "error",
    [DuplicateDictionaryNameError("Пример"), DuplicateOrganizationNameIn1CError("ООО «Пример»")],
)
def test_create_organization_feature_error_exits_transaction_unchanged(
    error: DuplicateDictionaryNameError | DuplicateOrganizationNameIn1CError,
) -> None:
    session, transaction = _session_with_transaction()
    feature = AsyncMock(side_effect=error)

    with (
        patch("sigma.modules.dictionaries.facade.create_organization_feature", feature),
        pytest.raises(type(error)) as caught,
    ):
        asyncio.run(DictionariesFacade(session).create_organization("Пример", "ООО «Пример»"))

    assert caught.value is error
    session.begin.assert_called_once_with()
    transaction.__aenter__.assert_awaited_once_with()
    transaction.__aexit__.assert_awaited_once()
    exit_args = transaction.__aexit__.await_args.args
    assert exit_args[0] is type(error)
    assert exit_args[1] is error
    assert exit_args[2] is not None


@pytest.mark.parametrize("restore", [False, True])
def test_organization_not_found_exits_transaction_unchanged(restore: bool) -> None:
    session, transaction = _session_with_transaction()
    error = OrganizationNotFoundError(uuid4())
    feature = AsyncMock(side_effect=error)
    feature_name = "restore_organization_feature" if restore else "archive_organization_feature"

    with (
        patch(f"sigma.modules.dictionaries.facade.{feature_name}", feature),
        pytest.raises(OrganizationNotFoundError) as caught,
    ):
        facade = DictionariesFacade(session)
        asyncio.run(
            facade.restore_organization(error.organization_id)
            if restore
            else facade.archive_organization(error.organization_id)
        )

    assert caught.value is error
    session.begin.assert_called_once_with()
    transaction.__aenter__.assert_awaited_once_with()
    transaction.__aexit__.assert_awaited_once()
    exit_args = transaction.__aexit__.await_args.args
    assert exit_args[0] is OrganizationNotFoundError
    assert exit_args[1] is error
    assert exit_args[2] is not None
