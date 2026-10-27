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
