from fastapi import FastAPI

from .facade import DictionariesDomainError, DictionariesFeatureError
from .presentation.articles import router as articles_router
from .presentation.categories import router as categories_router
from .presentation.cfos import router as cfos_router
from .presentation.error_mapping import dictionaries_error
from .presentation.mrps import router as mrps_router


def register(app: FastAPI) -> None:
    app.include_router(categories_router)
    app.include_router(articles_router)
    app.include_router(mrps_router)
    app.include_router(cfos_router)
    app.add_exception_handler(DictionariesDomainError, dictionaries_error)
    app.add_exception_handler(DictionariesFeatureError, dictionaries_error)
