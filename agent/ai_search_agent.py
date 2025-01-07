import asyncio
import logging
from datetime import timedelta, datetime
from typing import AsyncGenerator, List

import pytz
from langchain_core.documents import Document

from echelon.common.codec import jsondumps
from echelon.common.utils import score, merge_score, calculate_topic_activity
from echelon.operators.llm import EChartOpReq
from echelon.operators.llm.google_mindmap_op import GoogleMindMapOp
from echelon.operators.llm.related_questions_op import RelatedQuestionsOp, RelatedQuestionsReq, Questions
from echelon.operators.llm.search_answer_op import SearchAnswerOp, SearchAnswerReq
from echelon.operators.llm.x_mindmap_op import XmindMapOp, XmindMapReq, TwitterSummaryResp
from echelon.operators.search.searchapi import SearchApiOp, SearchApiReq
from echelon.operators.search.x import XSearchOp, XSearchReq, Media
from echelon.operators.search.x_count import XCountReq, XCountOp
from echelon.operators.web3.get_c_historical import GetCryptoHistoricalReq, GetCryptoHistorical
from echelon.operators.web3.get_c_latest import GetCryptoLatest, GetCryptoLatestReq
from echelon.operators.web3.get_c_score import get_crypto_platform_score, get_crypto_symbol_score
from echelon.operators.web3.get_d_markets import get_markets, get_markets_info
from echelon.repository.cmc_mapping import get_crypto_mapping, CmcCrypto

logger = logging.getLogger(__name__)


class AISearchSSE:

    @staticmethod
    def query_rewriting(data: list[str]):
        return {"event": "query_rewriting", "data": jsondumps(data)}

    @staticmethod
    def x_posts(data):
        list_r = []
        if data and isinstance(data, list):
            for d in data:
                if isinstance(d, Document):
                    list_r.append(d.metadata)

        return {"event": "x_posts", "data": jsondumps(list_r)}

    @staticmethod
    def google_answer(data: str):
        """"""
        return {"event": "google_answer", "data": data}

    @staticmethod
    def crypto(data: str):
        """"""
        return {"event": "crypto", "data": jsondumps(data)}

    @staticmethod
    def x_answer(data: str):
        """"""
        return {"event": "x_answer", "data": data}

    @staticmethod
    def related_questions(data: list[str]):
        return {"event": "related_questions", "data": jsondumps(data)}

    @staticmethod
    def mindmap(data: str):
        return {"event": "mindmap", "data": data}

    @staticmethod
    def images(data):
        return {"event": "images", "data": jsondumps(data)}

    @staticmethod
    def end():
        """"""
        return {"event": "end"}

    @staticmethod
    def crypto_latest(crypto_latest):
        if not crypto_latest:
            return
        return {"event": "crypto_latest", "data": jsondumps(crypto_latest)}

    @staticmethod
    def crypto_historical(crypto_latest):
        if not crypto_latest:
            return
        return {"event": "crypto_historical", "data": jsondumps(crypto_latest)}

    @staticmethod
    def d_markets(crypto_latest):
        if not crypto_latest:
            return
        return {"event": "d_markets", "data": jsondumps(crypto_latest)}

    @staticmethod
    def x_query_growth_score(score):
        return {"event": "x_query_growth_score", "data": jsondumps(score)}

    @staticmethod
    def token_transaction_growth(growth):
        return {"event": "token_transaction_growth", "data": growth}


class AISearchAgent(object):

    async def search(self, user_input: str) -> AsyncGenerator:
        org_user_input = user_input
        logger.info('User input is %s', org_user_input)

        # query_score_task = asyncio.create_task(self._get_query_score(org_user_input))
        crypto_task = asyncio.create_task(get_crypto_mapping(org_user_input))
        x_search_tasks = [self._x_search_single_query(query) for query in [org_user_input]]

        # try:
        #     search_querys = set()
        #     search_querys.add(user_input)
        #     querys = await QueryRewritingOp().predict(UserInputReq(user_input=user_input))
        #     if querys:
        #         for q in (querys.queries or []):
        #             search_querys.add(q)
        #
        #     yield AISearchSSE.query_rewriting(list(search_querys))
        # except Exception as e:
        #     logger.error(e)

        crypto = await crypto_task

        get_crypto_platform_score_task = None
        get_crypto_symbol_score_task = None
        if isinstance(crypto, CmcCrypto):
            logger.info(f"crypto is {jsondumps(crypto.model_dump())}")
            yield AISearchSSE.crypto(crypto.model_dump())
            get_crypto_latest_task = asyncio.create_task(self._get_crypto_latest(crypto.id))
            get_crypto_historical_task = asyncio.create_task(self._get_crypto_historical(crypto.id))
            get_crypto_platform_score_task = asyncio.create_task(
                get_crypto_platform_score(crypto.ca, crypto.platform))

            get_markets_task = asyncio.create_task(get_markets(crypto.ca, crypto.platform))
            get_markets_info_task = asyncio.create_task(get_markets_info(crypto.ca, crypto.platform))

            get_crypto_symbol_score_task = asyncio.create_task(get_crypto_symbol_score(crypto.symbol))

            markets_info = await get_markets_info_task
            crypto_latest = await get_crypto_latest_task
            if isinstance(markets_info, dict) and isinstance(crypto_latest, dict):
                try:
                    mcap = markets_info.get("data", {}).get("mcap", None)
                    if mcap:
                        dynamic_id = next(iter(crypto_latest['data']))
                        if dynamic_id in crypto_latest['data']:
                            crypto_latest['data'][dynamic_id]['quote']['USD']['market_cap'] = mcap
                except Exception as e:
                    pass

            crypto_historical = await get_crypto_historical_task

            if crypto_historical:
                yield AISearchSSE.crypto_latest(crypto_latest)
                yield AISearchSSE.crypto_historical(crypto_historical)
            else:
                d_markets = {}
                markets = await get_markets_task
                if isinstance(markets, dict):
                    d_markets.update(markets)
                if isinstance(markets_info, dict):
                    if d_markets:
                        d_markets.get("data", {}).update(markets_info.get("data", {}))
                    else:
                        d_markets.update(markets_info)
                yield AISearchSSE.d_markets(d_markets)

        x_search_results = await asyncio.gather(*x_search_tasks, return_exceptions=True)

        x_resources: List[Document] = []
        images: List[Media] = []

        for search_result in x_search_results:
            if isinstance(search_result, list):
                for x in search_result:
                    if isinstance(x, Document):
                        x_resources.append(x)
                    elif isinstance(x, Media):
                        images.append(x.model_dump())

        resources: List[Document] = []
        resources.extend(x_resources)

        x_mindmap_task = None
        if x_resources:
            x_mindmap_task = asyncio.create_task(self._x_mindmap_op(x_resources=x_resources))

        yield AISearchSSE.x_posts(resources)

        # related_questions_task = asyncio.create_task(
        #     self._gen_related_questions(user_input=org_user_input, resources=resources))

        try:
            x_answer = ""
            async for chunk in SearchAnswerOp().stream(SearchAnswerReq(user_input=user_input,
                                                                       resources=x_resources, )):
                x_answer += chunk
                yield AISearchSSE.x_answer(chunk)
        except Exception as e:
            logger.error(e)

        yield AISearchSSE.images(images)

        # related_questions = await related_questions_task
        # if related_questions and related_questions.questions:
        #     yield AISearchSSE.related_questions(related_questions.questions)
        # else:
        #     yield AISearchSSE.related_questions([])

        query_score = calculate_topic_activity(x_resources)
        crypto_platform_score = 0.0
        volume_score = 0.0
        market_cap_score = 0.0
        if get_crypto_platform_score_task:
            crypto_platform_score = await get_crypto_platform_score_task
        if get_crypto_symbol_score_task:
            volume_score, market_cap_score = await get_crypto_symbol_score_task

        merged_score = merge_score(off_chain_score=query_score,
                                   crypto_platform_score=crypto_platform_score,
                                   volume_score=volume_score,
                                   market_cap_score=market_cap_score)

        yield AISearchSSE.x_query_growth_score(merged_score)

        if x_mindmap_task:
            x_mindmap = await x_mindmap_task

            if isinstance(x_mindmap, TwitterSummaryResp):
                mindmap = f"# X\n\n"
                for s in x_mindmap.summaries:
                    mindmap += f"- {s.twitter_user_name} : {s.content_summary}\n\n"

                yield AISearchSSE.mindmap(mindmap)

        yield AISearchSSE.end()

    async def _google_mindmap_op(self, searchapi_answer: str):
        return await GoogleMindMapOp().predict(EChartOpReq(text=searchapi_answer))

    async def _x_mindmap_op(self, x_resources):
        return await XmindMapOp().predict(XmindMapReq(resources=x_resources))

    async def _x_search_single_query(self, query: str):
        try:
            return await XSearchOp().search(XSearchReq(query=query))
        except Exception as e:
            logger.error(e)
        return []

    async def _searchapi_search_single_query(self, query: str):
        return await SearchApiOp().search(SearchApiReq(query=query))

    async def _gen_related_questions(self, user_input: str, resources) -> Questions:
        return await RelatedQuestionsOp().predict(RelatedQuestionsReq(user_input=user_input, resources=resources))

    async def _get_crypto_latest(self, id):
        return await GetCryptoLatest().call(GetCryptoLatestReq(id=id))

    async def _get_crypto_historical(self, id):
        now = datetime.now(pytz.utc)
        one_hour_ago = now - timedelta(hours=8)
        return await GetCryptoHistorical().call(GetCryptoHistoricalReq(id=str(id),
                                                                       time_start=str(one_hour_ago),
                                                                       time_end=str(now)))

    async def _get_query_score(self, query: str):
        try:
            now = datetime.now(pytz.utc)
            end_1 = (now - timedelta(minutes=10)).isoformat()
            begin_1 = (now - timedelta(minutes=20)).isoformat()

            end_2 = (now - timedelta(minutes=70)).isoformat()
            begin_2 = (now - timedelta(minutes=80)).isoformat()

            r1 = await XCountOp().search(XCountReq(query=query, start_time=begin_1, end_time=end_1))
            r2 = await XCountOp().search(XCountReq(query=query, start_time=begin_2, end_time=end_2))

            if r2 >= 100 and r1 >= 100:
                return 3

            return score(r2, r1)
        except Exception:
            return 0
