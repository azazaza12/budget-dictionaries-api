from typing import ClassVar
from uuid import UUID


class DictionariesFeatureError(Exception):
    code: ClassVar[str]


class DuplicateDictionaryNameError(DictionariesFeatureError):
    code = "duplicate_dictionary_name"

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Dictionary name '{name}' already exists")


class CategoryNotFoundError(DictionariesFeatureError):
    code = "category_not_found"

    def __init__(self, category_id: UUID) -> None:
        self.category_id = category_id
        super().__init__(f"Category {category_id} was not found")


class CFONotFoundError(DictionariesFeatureError):
    code = "cfo_not_found"

    def __init__(self, cfo_id: UUID) -> None:
        self.cfo_id = cfo_id
        super().__init__(f"CFO {cfo_id} was not found")


class BudgetArticleNotFoundError(DictionariesFeatureError):
    code = "budget_article_not_found"

    def __init__(self, article_id: UUID) -> None:
        self.article_id = article_id
        super().__init__(f"Budget article {article_id} was not found")


class MRPNotFoundError(DictionariesFeatureError):
    code = "mrp_not_found"

    def __init__(self, mrp_id: UUID) -> None:
        self.mrp_id = mrp_id
        super().__init__(f"MRP {mrp_id} was not found")


class DuplicateSavingsDistributionRuleError(DictionariesFeatureError):
    code = "duplicate_savings_distribution_rule"

    def __init__(self, rule_id: UUID) -> None:
        self.rule_id = rule_id
        super().__init__(f"Savings distribution rule {rule_id} already exists")
