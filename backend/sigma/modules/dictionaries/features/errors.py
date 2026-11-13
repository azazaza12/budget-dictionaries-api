from typing import ClassVar
from uuid import UUID


class DictionariesFeatureError(Exception):
    code: ClassVar[str]


class DuplicateDictionaryNameError(DictionariesFeatureError):
    code = "duplicate_dictionary_name"
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class DuplicateOrganizationExternalNameError(DictionariesFeatureError):
    code = "duplicate_organization_external_name"

    def __init__(self, external_name: str) -> None:
        self.external_name = external_name
        super().__init__(f"Organization external name '{external_name}' already exists")


class OrganizationNotFoundError(DictionariesFeatureError):
    code = "organization_not_found"

    def __init__(self, organization_id: UUID) -> None:
        self.organization_id = organization_id
        super().__init__(f"Organization {organization_id} was not found")


class CategoryNotFoundError(DictionariesFeatureError):
    code = "category_not_found"
    category_id: UUID

    def __init__(self, category_id: UUID) -> None:
        self.category_id = category_id


class CFONotFoundError(DictionariesFeatureError):
    code = "cfo_not_found"
    cfo_id: UUID

    def __init__(self, cfo_id: UUID) -> None:
        self.cfo_id = cfo_id


class BudgetArticleNotFoundError(DictionariesFeatureError):
    code = "budget_article_not_found"
    article_id: UUID

    def __init__(self, article_id: UUID) -> None:
        self.article_id = article_id


class MRPNotFoundError(DictionariesFeatureError):
    code = "mrp_not_found"
    mrp_id: UUID

    def __init__(self, mrp_id: UUID) -> None:
        self.mrp_id = mrp_id


class DuplicateDistributionRuleError(DictionariesFeatureError):
    code = "duplicate_savings_distribution_rule"
    rule_id: UUID

    def __init__(self, rule_id: UUID) -> None:
        self.rule_id = rule_id


class DistributionRuleNotFoundError(DictionariesFeatureError):
    code = "savings_distribution_rule_not_found"
    rule_id: UUID

    def __init__(self, rule_id: UUID) -> None:
        self.rule_id = rule_id
