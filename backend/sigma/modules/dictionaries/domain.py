from dataclasses import dataclass, field
from uuid import UUID, uuid4


class DictionariesDomainError(Exception):
    pass


class InvalidDictionaryNameError(DictionariesDomainError):
    pass


class ArchivedCategoryError(DictionariesDomainError):
    pass


class ArticleCategoryMismatchError(DictionariesDomainError):
    pass


def clean_name(value: str) -> str:
    cleaned_value = " ".join(value.split())
    if not cleaned_value:
        raise InvalidDictionaryNameError("Dictionary name must not be empty")
    return cleaned_value


def normalize_name(value: str) -> str:
    return clean_name(value).casefold()


@dataclass(slots=True)
class Category:
    name: str
    id: UUID = field(default_factory=uuid4)
    is_archived: bool = False

    def __post_init__(self) -> None:
        self.name = clean_name(self.name)

    @property
    def normalized_name(self) -> str:
        return normalize_name(self.name)

    def rename(self, new_name: str) -> None:
        self.name = clean_name(new_name)

    def archive(self) -> None:
        self.is_archived = True

    def restore(self) -> None:
        self.is_archived = False

    def require_active(self) -> None:
        if self.is_archived:
            raise ArchivedCategoryError(f"Category {self.id} is archived")


@dataclass(slots=True)
class BudgetArticle:
    name: str
    category_id: UUID
    id: UUID = field(default_factory=uuid4)
    is_archived: bool = False

    def __post_init__(self) -> None:
        self.name = clean_name(self.name)

    @classmethod
    def create(cls, name: str, category: Category) -> BudgetArticle:
        category.require_active()
        return cls(name=name, category_id=category.id)

    @property
    def normalized_name(self) -> str:
        return normalize_name(self.name)

    def rename(self, new_name: str) -> None:
        self.name = clean_name(new_name)

    def archive(self) -> None:
        self.is_archived = True

    def restore(self, current_category: Category) -> None:
        if current_category.id != self.category_id:
            raise ArticleCategoryMismatchError(
                f"Article {self.id} does not belong to category {current_category.id}"
            )
        current_category.require_active()
        self.is_archived = False

    def move_to(self, target_category: Category) -> None:
        target_category.require_active()
        self.category_id = target_category.id
