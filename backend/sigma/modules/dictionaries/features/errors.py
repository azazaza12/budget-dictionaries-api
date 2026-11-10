from typing import ClassVar
from uuid import UUID


class DictionariesFeatureError(Exception):
    code: ClassVar[str]


class DuplicateDictionaryNameError(DictionariesFeatureError):
    code = "duplicate_dictionary_name"

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Dictionary name '{name}' already exists")


class DuplicateOrganizationNameIn1CError(DictionariesFeatureError):
    code = "duplicate_organization_name_in_1c"

    def __init__(self, name_in_1c: str) -> None:
        self.name_in_1c = name_in_1c
        super().__init__(f"Organization name in 1C '{name_in_1c}' already exists")


class OrganizationNotFoundError(DictionariesFeatureError):
    code = "organization_not_found"

    def __init__(self, organization_id: UUID) -> None:
        self.organization_id = organization_id
        super().__init__(f"Organization {organization_id} was not found")


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
