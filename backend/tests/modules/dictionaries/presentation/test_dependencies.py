from unittest.mock import MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from sigma.modules.dictionaries.presentation.dependencies import (
    get_dictionaries_facade,
)


def test_get_dictionaries_facade_uses_session() -> None:
    session = MagicMock(spec=AsyncSession)

    with patch(
        "sigma.modules.dictionaries.presentation.dependencies.DictionariesFacade"
    ) as facade_type:
        dictionaries = get_dictionaries_facade(session)

    facade_type.assert_called_once_with(session)
    assert dictionaries is facade_type.return_value
