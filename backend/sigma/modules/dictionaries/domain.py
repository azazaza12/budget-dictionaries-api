from dataclasses import dataclass, field
from typing import ClassVar
from uuid import UUID, uuid4


class DictionariesDomainError(Exception):
    code: ClassVar[str]


class InvalidDictionaryNameError(DictionariesDomainError):
    code = "invalid_dictionary_name"


class ArchivedCategoryError(DictionariesDomainError):
    code = "archived_category"

    def __init__(self, category_id: UUID) -> None:
        self.category_id = category_id
        super().__init__(f"Category {category_id} is archived")


class ArticleCategoryMismatchError(DictionariesDomainError):
    code = "article_category_mismatch"

    def __init__(
        self,
        article_id: UUID,
        expected_category_id: UUID,
        provided_category_id: UUID,
    ) -> None:
        self.article_id = article_id
        self.expected_category_id = expected_category_id
        self.provided_category_id = provided_category_id
        super().__init__(
            f"Article {article_id} belongs to category {expected_category_id}, "
            f"not {provided_category_id}"
        )


def clean_name(value: str) -> str:
    cleaned_value = " ".join(value.split())
    if not cleaned_value:
        raise InvalidDictionaryNameError("Dictionary name must not be empty")
    return cleaned_value


def normalize_name(value: str) -> str:
    return clean_name(value).casefold()


@dataclass(slots=True, kw_only=True)
class BaseDictionary:
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


@dataclass(slots=True, kw_only=True)
class Category(BaseDictionary):
    def restore(self) -> None:
        self.is_archived = False

    def require_active(self) -> None:
        if self.is_archived:
            raise ArchivedCategoryError(self.id)


@dataclass(slots=True, kw_only=True)
class BudgetArticle(BaseDictionary):
    category_id: UUID

    @classmethod
    def create(cls, name: str, category: Category) -> BudgetArticle:
        category.require_active()
        return cls(name=name, category_id=category.id)

    def restore(self, current_category: Category) -> None:
        if current_category.id != self.category_id:
            raise ArticleCategoryMismatchError(
                self.id,
                self.category_id,
                current_category.id,
            )
        current_category.require_active()
        self.is_archived = False

    def move_to(self, target_category: Category) -> None:
        target_category.require_active()
        self.category_id = target_category.id


@dataclass(slots=True, kw_only=True)
class MRP(BaseDictionary):
    def restore(self) -> None:
        self.is_archived = False


@dataclass(slots=True, kw_only=True)
class CFO(BaseDictionary):
    def restore(self) -> None:
        self.is_archived = False
