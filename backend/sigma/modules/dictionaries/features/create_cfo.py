from sigma.modules.dictionaries.domain import CFO
from sigma.modules.dictionaries.repository import CFORepository

from .errors import DuplicateDictionaryNameError


async def create_cfo(name: str, repository: CFORepository) -> CFO:
    cfo = CFO(name=name)
    if await repository.name_exists(cfo.normalized_name):
        raise DuplicateDictionaryNameError(cfo.name)
    await repository.add(cfo)
    return cfo
