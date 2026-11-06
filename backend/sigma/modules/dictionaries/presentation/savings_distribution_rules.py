from uuid import UUID

from fastapi import APIRouter, Depends, status

from .dependencies import DictionariesFacadeDependency, require_dictionaries_admin
from .schemas import (
    MRPView,
    SavingsDistributionRuleDetailsView,
    SavingsDistributionRuleInput,
    SavingsDistributionRuleView,
)

router = APIRouter(
    prefix="/dictionaries/savings-distribution-rules",
    tags=["dictionaries"],
)


@router.get("/recommendation")
async def recommend_mrp(
    cfo_id: UUID,
    budget_article_id: UUID,
    dictionaries: DictionariesFacadeDependency,
) -> MRPView | None:
    mrp = await dictionaries.find_mrp_by_savings_distribution_rule(cfo_id, budget_article_id)
    if mrp is None:
        return None

    return MRPView.model_validate(mrp)


@router.get("")
async def list_savings_distribution_rules(
    dictionaries: DictionariesFacadeDependency,
) -> list[SavingsDistributionRuleDetailsView]:
    items = await dictionaries.list_savings_distribution_rules()
    return [SavingsDistributionRuleDetailsView.model_validate(item) for item in items]


@router.post(
    "", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_dictionaries_admin)]
)
async def create_savings_distribution_rule(
    data: SavingsDistributionRuleInput, dictionaries: DictionariesFacadeDependency
) -> SavingsDistributionRuleView:
    rule = await dictionaries.create_savings_distribution_rule(
        data.cfo_id, data.budget_article_id, data.mrp_id
    )
    return SavingsDistributionRuleView.model_validate(rule)


@router.get("/{rule_id}")
async def get_savings_distribution_rule(
    rule_id: UUID, dictionaries: DictionariesFacadeDependency
) -> SavingsDistributionRuleView:
    rule = await dictionaries.get_savings_distribution_rule(rule_id)
    return SavingsDistributionRuleView.model_validate(rule)


@router.put("/{rule_id}", dependencies=[Depends(require_dictionaries_admin)])
async def update_savings_distribution_rule(
    rule_id: UUID,
    data: SavingsDistributionRuleInput,
    dictionaries: DictionariesFacadeDependency,
) -> SavingsDistributionRuleView:
    rule = await dictionaries.update_savings_distribution_rule(
        rule_id, data.cfo_id, data.budget_article_id, data.mrp_id
    )
    return SavingsDistributionRuleView.model_validate(rule)


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_dictionaries_admin)],
)
async def delete_savings_distribution_rule(
    rule_id: UUID, dictionaries: DictionariesFacadeDependency
) -> None:
    await dictionaries.delete_savings_distribution_rule(rule_id)
