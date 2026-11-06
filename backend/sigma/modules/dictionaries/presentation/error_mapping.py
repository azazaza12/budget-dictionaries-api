from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from sigma.modules.dictionaries.facade import (
    ArchivedBudgetArticleError,
    ArchivedCategoryError,
    ArchivedCFOError,
    ArchivedMRPError,
    ArticleCategoryMismatchError,
    BudgetArticleNotFoundError,
    CategoryNotFoundError,
    CFONotFoundError,
    DictionariesDomainError,
    DictionariesFeatureError,
    DuplicateDictionaryNameError,
    DuplicateSavingsDistributionRuleError,
    InvalidDictionaryNameError,
    MRPNotFoundError,
    SavingsDistributionRuleNotFoundError,
)

ERROR_STATUSES: dict[type[Exception], int] = {
    SavingsDistributionRuleNotFoundError: status.HTTP_404_NOT_FOUND,
    DuplicateSavingsDistributionRuleError: status.HTTP_409_CONFLICT,
    ArchivedCFOError: status.HTTP_409_CONFLICT,
    ArchivedBudgetArticleError: status.HTTP_409_CONFLICT,
    ArchivedMRPError: status.HTTP_409_CONFLICT,
    MRPNotFoundError: status.HTTP_404_NOT_FOUND,
    CFONotFoundError: status.HTTP_404_NOT_FOUND,
    CategoryNotFoundError: status.HTTP_404_NOT_FOUND,
    BudgetArticleNotFoundError: status.HTTP_404_NOT_FOUND,
    DuplicateDictionaryNameError: status.HTTP_409_CONFLICT,
    ArchivedCategoryError: status.HTTP_409_CONFLICT,
    ArticleCategoryMismatchError: status.HTTP_409_CONFLICT,
    InvalidDictionaryNameError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


async def dictionaries_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, (DictionariesDomainError, DictionariesFeatureError)):
        raise exc
    return JSONResponse(
        status_code=ERROR_STATUSES[type(exc)],
        content=jsonable_encoder({"code": exc.code, "context": vars(exc)}),
    )
