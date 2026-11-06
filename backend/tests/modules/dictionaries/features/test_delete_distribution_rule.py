import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import DistributionRule
from sigma.modules.dictionaries.features.delete_distribution_rule import (
    delete_distribution_rule,
)
from sigma.modules.dictionaries.features.errors import DistributionRuleNotFoundError
from sigma.modules.dictionaries.repository import DistributionRuleRepository


def test_delete_rule_removes_existing_rule() -> None:
    rule = DistributionRule(cfo_id=uuid4(), budget_article_id=uuid4(), mrp_id=uuid4())
    repository = MagicMock(spec=DistributionRuleRepository)
    repository.get = AsyncMock(return_value=rule)
    repository.delete = AsyncMock()

    result = asyncio.run(delete_distribution_rule(rule.id, repository))

    assert result is None
    repository.get.assert_awaited_once_with(rule.id)
    repository.delete.assert_awaited_once_with(rule)
    repository.add.assert_not_called()
    repository.save.assert_not_called()


def test_delete_missing_rule_is_rejected() -> None:
    rule_id = uuid4()
    repository = MagicMock(spec=DistributionRuleRepository)
    repository.get = AsyncMock(return_value=None)
    repository.delete = AsyncMock()

    with pytest.raises(DistributionRuleNotFoundError) as error:
        asyncio.run(delete_distribution_rule(rule_id, repository))

    assert error.value.rule_id == rule_id
    repository.get.assert_awaited_once_with(rule_id)
    repository.delete.assert_not_awaited()
