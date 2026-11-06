import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sigma.modules.dictionaries.domain import (
    CFO,
    MRP,
    BudgetArticle,
    Category,
    SavingsDistributionRule,
)
from sigma.modules.dictionaries.features.list_savings_distribution_rules import (
    list_savings_distribution_rules,
)
from sigma.modules.dictionaries.repository import (
    SavingsDistributionRuleDetails,
    SavingsDistributionRuleRepository,
)


@pytest.mark.parametrize("empty", [False, True])
def test_list_rules_returns_repository_items_without_changes(empty: bool) -> None:
    cfo = CFO(name="Закупки", is_archived=True)
    category = Category(name="Командировки")
    article = BudgetArticle(name="Билеты", category_id=category.id, is_archived=True)
    mrp = MRP(name="Иванов", is_archived=True)
    items = (
        []
        if empty
        else [
            SavingsDistributionRuleDetails(
                rule=SavingsDistributionRule(
                    cfo_id=cfo.id,
                    budget_article_id=article.id,
                    mrp_id=mrp.id,
                ),
                cfo=cfo,
                budget_article=article,
                category=category,
                mrp=mrp,
            )
        ]
    )
    repository = MagicMock(spec=SavingsDistributionRuleRepository)
    repository.list = AsyncMock(return_value=items)

    result = asyncio.run(list_savings_distribution_rules(repository))

    assert result is items
    repository.list.assert_awaited_once_with()
    repository.get.assert_not_called()
    repository.add.assert_not_called()
    repository.save.assert_not_called()
    repository.delete.assert_not_called()
