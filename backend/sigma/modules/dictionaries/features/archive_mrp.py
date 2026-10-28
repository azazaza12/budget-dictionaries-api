from uuid import UUID

from sigma.modules.dictionaries.domain import MRP
from sigma.modules.dictionaries.repository import MRPRepository

from .errors import MRPNotFoundError


async def archive_mrp(mrp_id: UUID, repository: MRPRepository) -> MRP:
    mrp = await repository.get(mrp_id)
    if mrp is None:
        raise MRPNotFoundError(mrp_id)
    if mrp.is_archived:
        return mrp
    mrp.archive()
    await repository.save(mrp)
    return mrp
