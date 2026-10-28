from uuid import UUID

from sigma.modules.dictionaries.domain import MRP, normalize_name
from sigma.modules.dictionaries.repository import MRPRepository

from .errors import DuplicateDictionaryNameError, MRPNotFoundError


async def rename_mrp(mrp_id: UUID, new_name: str, repository: MRPRepository) -> MRP:
    mrp = await repository.get(mrp_id)
    if mrp is None:
        raise MRPNotFoundError(mrp_id)

    normalized_name = normalize_name(new_name)
    if await repository.name_exists(normalized_name, exclude_id=mrp_id):
        raise DuplicateDictionaryNameError(new_name)

    mrp.rename(new_name)
    await repository.save(mrp)
    return mrp
