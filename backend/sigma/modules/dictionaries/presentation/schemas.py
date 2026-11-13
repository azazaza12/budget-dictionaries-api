from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MRPInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str


class MRPView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    is_archived: bool


class CFOInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str


class CFOView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    is_archived: bool


class CategoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str


class BudgetArticleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category_id: UUID


class BudgetArticleCategoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: UUID


class BudgetArticleNameInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str


class CategoryView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    is_archived: bool


class BudgetArticleView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    category_id: UUID
    is_archived: bool


class DistributionRuleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cfo_id: UUID
    budget_article_id: UUID
    mrp_id: UUID


class DistributionRuleView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cfo_id: UUID
    budget_article_id: UUID
    mrp_id: UUID


class DistributionRuleDetailsView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule: DistributionRuleView
    cfo: CFOView
    budget_article: BudgetArticleView
    category: CategoryView
    mrp: MRPView


class OrganizationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    external_name: str


class OrganizationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    external_name: str
    is_archived: bool
