from sigma.modules.dictionaries.domain import MRP
from sigma.modules.dictionaries.repository import MRPRepository


async def list_mrps(
    repository: MRPRepository,
    *,
    include_archived: bool = False,
) -> list[MRP]:
    return await repository.list(include_archived=include_archived)
