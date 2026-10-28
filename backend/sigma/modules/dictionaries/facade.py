from uuid import UUID

from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .domain import (
    CFO,
    ArchivedCategoryError,
    ArticleCategoryMismatchError,
    BudgetArticle,
    Category,
    DictionariesDomainError,
    InvalidDictionaryNameError,
)
from .features.archive_article import archive_article as archive_article_feature
from .features.archive_category import archive_category as archive_category_feature
from .features.archive_cfo import archive_cfo as archive_cfo_feature
from .features.create_article import create_article as create_article_feature
from .features.create_category import create_category as create_category_feature
from .features.create_cfo import create_cfo as create_cfo_feature
from .features.errors import (
    BudgetArticleNotFoundError,
    CategoryNotFoundError,
    CFONotFoundError,
    DictionariesFeatureError,
    DuplicateDictionaryNameError,
)
from .features.list_articles import list_articles as list_articles_feature
from .features.list_categories import list_categories as list_categories_feature
from .features.list_cfos import list_cfos as list_cfos_feature
from .features.move_article import move_article as move_article_feature
from .features.rename_article import rename_article as rename_article_feature
from .features.rename_category import rename_category as rename_category_feature
from .features.rename_cfo import rename_cfo as rename_cfo_feature
from .features.restore_article import restore_article as restore_article_feature
from .features.restore_category import restore_category as restore_category_feature
from .features.restore_cfo import restore_cfo as restore_cfo_feature
from .repository import (
    SqlAlchemyBudgetArticleRepository,
    SqlAlchemyCategoryRepository,
    SqlAlchemyCFORepository,
)

__all__ = (
    "ArchivedCategoryError",
    "ArticleCategoryMismatchError",
    "BudgetArticleNotFoundError",
    "CFONotFoundError",
    "CategoryNotFoundError",
    "DictionariesDomainError",
    "DictionariesFacade",
    "DictionariesFeatureError",
    "DuplicateDictionaryNameError",
    "InvalidDictionaryNameError",
)


def _is_duplicate_cfo_name(error: IntegrityError) -> bool:
    # SQLAlchemy's asyncpg adapter preserves the driver error as its cause.
    cause = error.orig.__cause__ if error.orig is not None else None
    return (
        isinstance(cause, UniqueViolationError)
        and getattr(cause, "constraint_name", None) == "uq_cfo_normalized_name"
    )


class DictionariesFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._category_repository = SqlAlchemyCategoryRepository(session)
        self._article_repository = SqlAlchemyBudgetArticleRepository(session)
        self._cfo_repository = SqlAlchemyCFORepository(session)

    async def create_category(self, name: str) -> Category:
        async with self._session.begin():
            return await create_category_feature(name, self._category_repository)

    async def rename_category(self, category_id: UUID, new_name: str) -> Category:
        async with self._session.begin():
            return await rename_category_feature(category_id, new_name, self._category_repository)

    async def restore_category(self, category_id: UUID) -> Category:
        async with self._session.begin():
            return await restore_category_feature(category_id, self._category_repository)

    async def archive_category(self, category_id: UUID) -> Category:
        async with self._session.begin():
            return await archive_category_feature(
                category_id, self._category_repository, self._article_repository
            )

    async def list_categories(self, *, include_archived: bool = False) -> list[Category]:
        return await list_categories_feature(
            self._category_repository, include_archived=include_archived
        )

    async def create_article(self, name: str, category_id: UUID) -> BudgetArticle:
        async with self._session.begin():
            return await create_article_feature(
                name,
                category_id,
                self._category_repository,
                self._article_repository,
            )

    async def rename_article(self, article_id: UUID, new_name: str) -> BudgetArticle:
        async with self._session.begin():
            return await rename_article_feature(
                article_id,
                new_name,
                self._article_repository,
            )

    async def move_article(
        self,
        article_id: UUID,
        target_category_id: UUID,
    ) -> BudgetArticle:
        async with self._session.begin():
            return await move_article_feature(
                article_id,
                target_category_id,
                self._article_repository,
                self._category_repository,
            )

    async def restore_article(self, article_id: UUID) -> BudgetArticle:
        async with self._session.begin():
            return await restore_article_feature(
                article_id,
                self._article_repository,
                self._category_repository,
            )

    async def archive_article(self, article_id: UUID) -> BudgetArticle:
        async with self._session.begin():
            return await archive_article_feature(
                article_id,
                self._article_repository,
            )

    async def list_articles(
        self,
        *,
        include_archived: bool = False,
    ) -> list[BudgetArticle]:
        return await list_articles_feature(
            self._article_repository,
            include_archived=include_archived,
        )

    async def create_cfo(self, name: str) -> CFO:
        try:
            async with self._session.begin():
                return await create_cfo_feature(name, self._cfo_repository)
        except IntegrityError as error:
            if _is_duplicate_cfo_name(error):
                raise DuplicateDictionaryNameError(name) from error
            raise

    async def rename_cfo(self, cfo_id: UUID, new_name: str) -> CFO:
        try:
            async with self._session.begin():
                return await rename_cfo_feature(cfo_id, new_name, self._cfo_repository)
        except IntegrityError as error:
            if _is_duplicate_cfo_name(error):
                raise DuplicateDictionaryNameError(new_name) from error
            raise

    async def archive_cfo(self, cfo_id: UUID) -> CFO:
        async with self._session.begin():
            return await archive_cfo_feature(cfo_id, self._cfo_repository)

    async def restore_cfo(self, cfo_id: UUID) -> CFO:
        async with self._session.begin():
            return await restore_cfo_feature(cfo_id, self._cfo_repository)

    async def list_cfos(self, *, include_archived: bool = False) -> list[CFO]:
        return await list_cfos_feature(self._cfo_repository, include_archived=include_archived)
