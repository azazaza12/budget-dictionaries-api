from sigma.modules.dictionaries.domain import MRP
from sigma.modules.dictionaries.repository import MRPRepository

from .errors import DuplicateDictionaryNameError


async def create_mrp(name: str, repository: MRPRepository) -> MRP:
    mrp = MRP(name=name)
    if await repository.name_exists(mrp.normalized_name):
        raise DuplicateDictionaryNameError(mrp.name)
    await repository.add(mrp)
    return mrp
