from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .domain import (
    MRP,
    ArchivedCategoryError,
    ArticleCategoryMismatchError,
    BudgetArticle,
    Category,
    DictionariesDomainError,
    InvalidDictionaryNameError,
)
from .features.archive_article import archive_article as archive_article_feature
from .features.archive_category import archive_category as archive_category_feature
from .features.archive_mrp import archive_mrp as archive_mrp_feature
from .features.create_article import create_article as create_article_feature
from .features.create_category import create_category as create_category_feature
from .features.create_mrp import create_mrp as create_mrp_feature
from .features.errors import (
    BudgetArticleNotFoundError,
    CategoryNotFoundError,
    DictionariesFeatureError,
    DuplicateDictionaryNameError,
    MRPNotFoundError,
)
from .features.list_articles import list_articles as list_articles_feature
from .features.list_categories import list_categories as list_categories_feature
from .features.list_mrps import list_mrps as list_mrps_feature
from .features.move_article import move_article as move_article_feature
from .features.rename_article import rename_article as rename_article_feature
from .features.rename_category import rename_category as rename_category_feature
from .features.rename_mrp import rename_mrp as rename_mrp_feature
from .features.restore_article import restore_article as restore_article_feature
from .features.restore_category import restore_category as restore_category_feature
from .features.restore_mrp import restore_mrp as restore_mrp_feature
from .repository import (
    SqlAlchemyBudgetArticleRepository,
    SqlAlchemyCategoryRepository,
    SqlAlchemyMRPRepository,
)

__all__ = (
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
)


class DictionariesFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._category_repository = SqlAlchemyCategoryRepository(session)
        self._article_repository = SqlAlchemyBudgetArticleRepository(session)
        self._mrp_repository = SqlAlchemyMRPRepository(session)

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

    async def create_mrp(self, name: str) -> MRP:
        async with self._session.begin():
            return await create_mrp_feature(name, self._mrp_repository)

    async def rename_mrp(self, mrp_id: UUID, new_name: str) -> MRP:
        async with self._session.begin():
            return await rename_mrp_feature(mrp_id, new_name, self._mrp_repository)

    async def archive_mrp(self, mrp_id: UUID) -> MRP:
        async with self._session.begin():
            return await archive_mrp_feature(mrp_id, self._mrp_repository)

    async def restore_mrp(self, mrp_id: UUID) -> MRP:
        async with self._session.begin():
            return await restore_mrp_feature(mrp_id, self._mrp_repository)

    async def list_mrps(self, *, include_archived: bool = False) -> list[MRP]:
        return await list_mrps_feature(self._mrp_repository, include_archived=include_archived)
