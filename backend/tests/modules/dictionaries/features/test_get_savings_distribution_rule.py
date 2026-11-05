import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import SavingsDistributionRule
from sigma.modules.dictionaries.features.errors import SavingsDistributionRuleNotFoundError
from sigma.modules.dictionaries.features.get_savings_distribution_rule import (
    get_savings_distribution_rule,
)
from sigma.modules.dictionaries.repository import SavingsDistributionRuleRepository


def test_get_rule_returns_existing_rule() -> None:
    rule = SavingsDistributionRule(cfo_id=uuid4(), budget_article_id=uuid4(), mrp_id=uuid4())
    repository = MagicMock(spec=SavingsDistributionRuleRepository)
    repository.get = AsyncMock(return_value=rule)

    result = asyncio.run(get_savings_distribution_rule(rule.id, repository))

    assert result is rule
    repository.get.assert_awaited_once_with(rule.id)
    repository.add.assert_not_called()
    repository.save.assert_not_called()
    repository.delete.assert_not_called()


def test_get_missing_rule_is_rejected() -> None:
    rule_id = uuid4()
    repository = MagicMock(spec=SavingsDistributionRuleRepository)
    repository.get = AsyncMock(return_value=None)

    with pytest.raises(SavingsDistributionRuleNotFoundError) as error:
        asyncio.run(get_savings_distribution_rule(rule_id, repository))

    assert error.value.rule_id == rule_id
    repository.get.assert_awaited_once_with(rule_id)
    repository.add.assert_not_called()
    repository.save.assert_not_called()
    repository.delete.assert_not_called()
