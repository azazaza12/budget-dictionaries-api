from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from sigma.modules.dictionaries.facade import DictionariesFacade
from sigma.shared.db import get_session


def get_dictionaries_facade(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DictionariesFacade:
    return DictionariesFacade(session)


DictionariesFacadeDependency = Annotated[DictionariesFacade, Depends(get_dictionaries_facade)]
