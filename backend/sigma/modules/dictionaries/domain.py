from dataclasses import dataclass, field
from typing import ClassVar
from uuid import UUID, uuid4


class DictionariesDomainError(Exception):
    code: ClassVar[str]


class InvalidDictionaryNameError(DictionariesDomainError):
    code = "invalid_dictionary_name"


class ArchivedCategoryError(DictionariesDomainError):
    code = "archived_category"
    category_id: UUID

    def __init__(self, category_id: UUID) -> None:
        self.category_id = category_id


class ArchivedCFOError(DictionariesDomainError):
    code = "archived_cfo"
    cfo_id: UUID

    def __init__(self, cfo_id: UUID) -> None:
        self.cfo_id = cfo_id


class ArchivedBudgetArticleError(DictionariesDomainError):
    code = "archived_budget_article"
    article_id: UUID

    def __init__(self, article_id: UUID) -> None:
        self.article_id = article_id


class ArchivedMRPError(DictionariesDomainError):
    code = "archived_mrp"
    mrp_id: UUID

    def __init__(self, mrp_id: UUID) -> None:
        self.mrp_id = mrp_id


class ArticleCategoryMismatchError(DictionariesDomainError):
    code = "article_category_mismatch"
    article_id: UUID
    expected_category_id: UUID
    provided_category_id: UUID

    def __init__(
        self,
        article_id: UUID,
        expected_category_id: UUID,
        provided_category_id: UUID,
    ) -> None:
        self.article_id = article_id
        self.expected_category_id = expected_category_id
        self.provided_category_id = provided_category_id


def clean_name(value: str) -> str:
    cleaned_value = " ".join(value.split())
    if not cleaned_value:
        raise InvalidDictionaryNameError("Dictionary name must not be empty")
    return cleaned_value


def normalize_name(value: str) -> str:
    return clean_name(value).casefold()


def normalize_external_name(value: str) -> str:
    cleaned_name = clean_name(value)
    quote_translation = str.maketrans({"«": '"', "»": '"', "“": '"', "”": '"', "„": '"'})
    return cleaned_name.translate(quote_translation).casefold()


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

    def require_active(self) -> None:
        if self.is_archived:
            raise ArchivedBudgetArticleError(self.id)

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

    def require_active(self) -> None:
        if self.is_archived:
            raise ArchivedMRPError(self.id)


@dataclass(slots=True, kw_only=True)
class CFO(BaseDictionary):
    def restore(self) -> None:
        self.is_archived = False

    def require_active(self) -> None:
        if self.is_archived:
            raise ArchivedCFOError(self.id)


@dataclass(kw_only=True, slots=True)
class DistributionRule:
    id: UUID = field(default_factory=uuid4)
    cfo_id: UUID
    budget_article_id: UUID
    mrp_id: UUID

    @classmethod
    def create(cls, cfo: CFO, budget_article: BudgetArticle, mrp: MRP) -> DistributionRule:
        cfo.require_active()
        budget_article.require_active()
        mrp.require_active()
        return cls(cfo_id=cfo.id, budget_article_id=budget_article.id, mrp_id=mrp.id)

    def update(self, cfo: CFO, budget_article: BudgetArticle, mrp: MRP) -> None:
        if cfo.id != self.cfo_id:
            cfo.require_active()
        if budget_article.id != self.budget_article_id:
            budget_article.require_active()
        if mrp.id != self.mrp_id:
            mrp.require_active()
        self.cfo_id = cfo.id
        self.budget_article_id = budget_article.id
        self.mrp_id = mrp.id


@dataclass(slots=True, kw_only=True)
class Organization(BaseDictionary):
    external_name: str

    def __post_init__(self) -> None:
        self.name = clean_name(self.name)
        self.external_name = clean_name(self.external_name)

    @property
    def normalized_external_name(self) -> str:
        return normalize_external_name(self.external_name)

    def restore(self) -> None:
        self.is_archived = False

    def rename_external_name(self, new_name: str) -> None:
        cleaned_name = clean_name(new_name)
        self.external_name = cleaned_name
