from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from sigma.modules.dictionaries.facade import (
    ArchivedCategoryError,
    ArticleCategoryMismatchError,
    BudgetArticleNotFoundError,
    CategoryNotFoundError,
    CFONotFoundError,
    DictionariesDomainError,
    DictionariesFeatureError,
    DuplicateDictionaryNameError,
    DuplicateOrganizationExternalNameError,
    InvalidDictionaryNameError,
    MRPNotFoundError,
    OrganizationNotFoundError,
)

ERROR_STATUSES: dict[type[Exception], int] = {
    MRPNotFoundError: status.HTTP_404_NOT_FOUND,
    CFONotFoundError: status.HTTP_404_NOT_FOUND,
    CategoryNotFoundError: status.HTTP_404_NOT_FOUND,
    BudgetArticleNotFoundError: status.HTTP_404_NOT_FOUND,
    DuplicateDictionaryNameError: status.HTTP_409_CONFLICT,
    ArchivedCategoryError: status.HTTP_409_CONFLICT,
    ArticleCategoryMismatchError: status.HTTP_409_CONFLICT,
    InvalidDictionaryNameError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    OrganizationNotFoundError: status.HTTP_404_NOT_FOUND,
    DuplicateOrganizationExternalNameError: status.HTTP_409_CONFLICT,
}


async def dictionaries_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, (DictionariesDomainError, DictionariesFeatureError)):
        raise exc
    return JSONResponse(
        status_code=ERROR_STATUSES[type(exc)],
        content=jsonable_encoder({"code": exc.code, "context": vars(exc)}),
    )
