from typing import List, TypedDict, Annotated, Optional

from pydantic import BaseModel

from echelon.agent import recall_market_cap_coins, filter_coins_by_platform, search_derivative_new_coins, rank_coins, \
    BaseGraphNode, state_overwrite


class NewCoinsRecommendReq(BaseModel):
    large_cap_million: int = 10
    large_cap_count: int = 10
    platform_slug: str = 'solana'


class NewCoinsRecommendResp(BaseModel):
    new_coins: List[dict]


class NewCoinsRecommendState(TypedDict):
    recall: Annotated[Optional[List[dict]], state_overwrite]


class FilterCoinsbyPlatformGraphNode(BaseGraphNode):

    @classmethod
    def node_name(cls) -> str:
        return 'filter-coins-by-platform-node'

    async def _func(self, state: NewCoinsRecommendState):
        pass


class NewCoinsRecommendBotAgent(object):

    async def recommend(self, req: NewCoinsRecommendReq) -> NewCoinsRecommendResp:
        large_cap_coins = await recall_market_cap_coins(req.large_cap_million, req.large_cap_count)

        large_cap_coins = await filter_coins_by_platform(large_cap_coins, req.platform_slug)

        large_cap_derivative_coins = await search_derivative_new_coins(large_cap_coins)

        recommended_new_coins = await rank_coins(large_cap_derivative_coins)

        return recommended_new_coins
