from sigma.modules.dictionaries.domain import CFO
from sigma.modules.dictionaries.repository import CFORepository


async def list_cfos(
    repository: CFORepository,
    *,
    include_archived: bool = False,
) -> list[CFO]:
    return await repository.list(include_archived=include_archived)
