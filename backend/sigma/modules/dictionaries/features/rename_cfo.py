from uuid import UUID

from sigma.modules.dictionaries.domain import CFO, normalize_name
from sigma.modules.dictionaries.repository import CFORepository

from .errors import CFONotFoundError, DuplicateDictionaryNameError


async def rename_cfo(cfo_id: UUID, new_name: str, repository: CFORepository) -> CFO:
    cfo = await repository.get(cfo_id)
    if cfo is None:
        raise CFONotFoundError(cfo_id)

    normalized_name = normalize_name(new_name)
    if await repository.name_exists(normalized_name, exclude_id=cfo_id):
        raise DuplicateDictionaryNameError(new_name)

    cfo.rename(new_name)
    await repository.save(cfo)
    return cfo
