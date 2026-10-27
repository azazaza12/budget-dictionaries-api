from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from sigma.modules.dictionaries.facade import (
    ArchivedCategoryError,
    ArticleCategoryMismatchError,
    BudgetArticleNotFoundError,
    CategoryNotFoundError,
    DictionariesDomainError,
    DictionariesFeatureError,
    DuplicateDictionaryNameError,
    InvalidDictionaryNameError,
)

ERROR_STATUSES: dict[type[Exception], int] = {
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
