from uuid import UUID

from sigma.modules.dictionaries.domain import CFO
from sigma.modules.dictionaries.repository import CFORepository

from .errors import CFONotFoundError


async def restore_cfo(cfo_id: UUID, repository: CFORepository) -> CFO:
    cfo = await repository.get(cfo_id)
    if cfo is None:
        raise CFONotFoundError(cfo_id)
    if not cfo.is_archived:
        return cfo

    cfo.restore()
    await repository.save(cfo)
    return cfo
