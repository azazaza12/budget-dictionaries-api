from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .domain import CFO, MRP, BudgetArticle, Category, SavingsDistributionRule
from .models import (
    BudgetArticleModel,
    CategoryModel,
    CFOModel,
    MRPModel,
    SavingsDistributionRuleModel,
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


class MRPRepository(Protocol):
    async def get(self, mrp_id: UUID) -> MRP | None: ...

    async def add(self, mrp: MRP) -> None: ...

    async def list(self, *, include_archived: bool = False) -> list[MRP]: ...

    async def name_exists(
        self, normalized_name: str, *, exclude_id: UUID | None = None
    ) -> bool: ...

    async def save(self, mrp: MRP) -> None: ...


class CFORepository(Protocol):
    async def get(self, cfo_id: UUID) -> CFO | None: ...

    async def add(self, cfo: CFO) -> None: ...

    async def list(self, *, include_archived: bool = False) -> list[CFO]: ...

    async def save(self, cfo: CFO) -> None: ...

    async def name_exists(
        self, normalized_name: str, *, exclude_id: UUID | None = None
    ) -> bool: ...


class SavingsDistributionRuleRepository(Protocol):
    async def get(self, rule_id: UUID) -> SavingsDistributionRule | None: ...

    async def add(self, rule: SavingsDistributionRule) -> None: ...

    async def find_by_pair(
        self, cfo_id: UUID, budget_article_id: UUID
    ) -> SavingsDistributionRule | None: ...

    async def save(self, rule: SavingsDistributionRule) -> None: ...


class SqlAlchemyCategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: CategoryModel) -> Category:
        return Category(id=model.id, name=model.name, is_archived=model.is_archived)

    @staticmethod
    def _to_model(category: Category) -> CategoryModel:
        return CategoryModel(
            id=category.id,
            name=category.name,
            is_archived=category.is_archived,
            normalized_name=category.normalized_name,
        )

    async def get(self, category_id: UUID) -> Category | None:
        model = await self._session.get(CategoryModel, category_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def add(self, category: Category) -> None:
        self._session.add(self._to_model(category))

    async def list(self, *, include_archived: bool = False) -> list[Category]:
        statement = select(CategoryModel)
        if not include_archived:
            statement = statement.where(CategoryModel.is_archived.is_(False))

        statement = statement.order_by(CategoryModel.normalized_name, CategoryModel.id)
        models = (await self._session.scalars(statement)).all()
        return [self._to_domain(model) for model in models]

    async def name_exists(self, normalized_name: str, *, exclude_id: UUID | None = None) -> bool:
        query = select(CategoryModel.id).where(CategoryModel.normalized_name == normalized_name)
        if exclude_id is not None:
            query = query.where(CategoryModel.id != exclude_id)

        statement = select(query.exists())
        return bool(await self._session.scalar(statement))

    async def save(self, category: Category) -> None:
        await self._session.merge(self._to_model(category))


class SqlAlchemyBudgetArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: BudgetArticleModel) -> BudgetArticle:
        return BudgetArticle(
            id=model.id,
            name=model.name,
            is_archived=model.is_archived,
            category_id=model.category_id,
        )

    @staticmethod
    def _to_model(budget_article: BudgetArticle) -> BudgetArticleModel:
        return BudgetArticleModel(
            id=budget_article.id,
            name=budget_article.name,
            is_archived=budget_article.is_archived,
            category_id=budget_article.category_id,
            normalized_name=budget_article.normalized_name,
        )

    async def get(self, id: UUID) -> BudgetArticle | None:
        model = await self._session.get(BudgetArticleModel, id)
        if model is None:
            return None
        return self._to_domain(model)

    async def add(self, budget_article: BudgetArticle) -> None:
        model = self._to_model(budget_article)
        self._session.add(model)

    async def list(self, *, include_archived: bool = False) -> list[BudgetArticle]:
        statement = select(BudgetArticleModel)
        if not include_archived:
            statement = statement.where(BudgetArticleModel.is_archived.is_(False))
        statement = statement.order_by(BudgetArticleModel.normalized_name, BudgetArticleModel.id)
        models = (await self._session.scalars(statement)).all()
        return [self._to_domain(model) for model in models]

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
        return [self._to_domain(model) for model in models]

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
        model = self._to_model(budget_article)
        await self._session.merge(model)


class SqlAlchemyMRPRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: MRPModel) -> MRP:
        return MRP(id=model.id, name=model.name, is_archived=model.is_archived)

    @staticmethod
    def _to_model(mrp: MRP) -> MRPModel:
        return MRPModel(
            id=mrp.id,
            name=mrp.name,
            normalized_name=mrp.normalized_name,
            is_archived=mrp.is_archived,
        )

    async def get(self, mrp_id: UUID) -> MRP | None:
        model = await self._session.get(MRPModel, mrp_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def add(self, mrp: MRP) -> None:
        self._session.add(self._to_model(mrp))

    async def list(self, *, include_archived: bool = False) -> list[MRP]:
        statement = select(MRPModel)
        if not include_archived:
            statement = statement.where(MRPModel.is_archived.is_(False))
        statement = statement.order_by(MRPModel.normalized_name, MRPModel.id)
        models = (await self._session.scalars(statement)).all()
        return [self._to_domain(model) for model in models]

    async def name_exists(self, normalized_name: str, *, exclude_id: UUID | None = None) -> bool:
        query = select(MRPModel.id).where(MRPModel.normalized_name == normalized_name)
        if exclude_id is not None:
            query = query.where(MRPModel.id != exclude_id)
        statement = select(query.exists())
        return bool(await self._session.scalar(statement))

    async def save(self, mrp: MRP) -> None:
        await self._session.merge(self._to_model(mrp))


class SqlAlchemyCFORepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: CFOModel) -> CFO:
        return CFO(id=model.id, name=model.name, is_archived=model.is_archived)

    @staticmethod
    def _to_model(cfo: CFO) -> CFOModel:
        return CFOModel(
            id=cfo.id,
            name=cfo.name,
            normalized_name=cfo.normalized_name,
            is_archived=cfo.is_archived,
        )

    async def get(self, cfo_id: UUID) -> CFO | None:
        model = await self._session.get(CFOModel, cfo_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def add(self, cfo: CFO) -> None:
        cfo_model = self._to_model(cfo)
        self._session.add(cfo_model)

    async def list(self, *, include_archived: bool = False) -> list[CFO]:
        statement = select(CFOModel)
        if not include_archived:
            statement = statement.where(CFOModel.is_archived.is_(False))
        statement = statement.order_by(CFOModel.normalized_name, CFOModel.id)
        models = (await self._session.scalars(statement)).all()
        return [self._to_domain(model) for model in models]

    async def save(self, cfo: CFO) -> None:
        model = self._to_model(cfo)
        await self._session.merge(model)

    async def name_exists(self, normalized_name: str, *, exclude_id: UUID | None = None) -> bool:
        query = select(CFOModel.id).where(CFOModel.normalized_name == normalized_name)
        if exclude_id is not None:
            query = query.where(CFOModel.id != exclude_id)
        statement = select(query.exists())
        return bool(await self._session.scalar(statement))


class SqlAlchemySavingsDistributionRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: SavingsDistributionRuleModel) -> SavingsDistributionRule:
        return SavingsDistributionRule(
            id=model.id,
            cfo_id=model.cfo_id,
            budget_article_id=model.budget_article_id,
            mrp_id=model.mrp_id,
        )

    @staticmethod
    def _to_model(rule: SavingsDistributionRule) -> SavingsDistributionRuleModel:
        return SavingsDistributionRuleModel(
            id=rule.id,
            cfo_id=rule.cfo_id,
            budget_article_id=rule.budget_article_id,
            mrp_id=rule.mrp_id,
        )

    async def get(self, rule_id: UUID) -> SavingsDistributionRule | None:
        model = await self._session.get(SavingsDistributionRuleModel, rule_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def add(self, rule: SavingsDistributionRule) -> None:
        model = self._to_model(rule)
        self._session.add(model)

    async def find_by_pair(
        self, cfo_id: UUID, budget_article_id: UUID
    ) -> SavingsDistributionRule | None:
        statement = select(SavingsDistributionRuleModel).where(
            SavingsDistributionRuleModel.cfo_id == cfo_id,
            SavingsDistributionRuleModel.budget_article_id == budget_article_id,
        )
        model = await self._session.scalar(statement)
        if model is None:
            return None
        return self._to_domain(model)

    async def save(self, rule: SavingsDistributionRule) -> None:
        await self._session.merge(self._to_model(rule))
