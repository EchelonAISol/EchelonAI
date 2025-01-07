import logging
import time
import uuid
from abc import abstractmethod
from typing import TypedDict, Type, Optional, Any, List, AsyncGenerator

import requests
from langchain_core.callbacks import Callbacks
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel, computed_field

from echelon.chains.log_callback import LLMLogCallbackHandler

logger = logging.getLogger(__name__)


def state_overwrite(x, y):
    return y


def state_return_old_if_present(old, new):
    if not old:
        return new
    return old


def state_merge_list(left, right):
    if not isinstance(left, list):
        left = [left]
    if not isinstance(right, list):
        right = [right]
    return left + right


def create_agent_runnable_config(max_concurrency: int = None,
                                 thread_id: str = None,
                                 callbacks: Callbacks = None) -> RunnableConfig:
    config = RunnableConfig(callbacks=callbacks, )
    configurable = {
        'thread_id': thread_id or str(uuid.uuid4()),
        'thread_ts': time.time()
    }
    if max_concurrency:
        configurable['max_concurrency'] = max_concurrency
        config.update({'max_concurrency': max_concurrency})
    config.update({"configurable": configurable})
    return config


class BaseGraphNode(BaseModel):

    @classmethod
    @abstractmethod
    def node_name(cls) -> str:
        return cls.__name__

    @abstractmethod
    async def _func(self, state: TypedDict):
        pass

    def join_graph(self, graph: StateGraph):
        graph.add_node(self.__class__.node_name(), self.func)

    async def func(self, state: TypedDict):
        await self._func(state)
        return state

    async def _stream_output(self, state: TypedDict):
        raise NotImplementedError()


class BaseGraphAgent(BaseModel):
    _graph_nodes: list[BaseGraphNode] = None

    @abstractmethod
    def _get_state_type(self) -> Type:
        raise NotImplementedError()

    @abstractmethod
    def _get_nodes(self) -> list[BaseGraphNode]:
        raise NotImplementedError()

    def _set_edges(self, builder: StateGraph) -> None:
        nodes = self._get_nodes()

        def get_node_name(node):
            node_name = ''
            if isinstance(node, BaseGraphNode):
                node_name = node.node_name()
            return node_name

        entry_name = get_node_name(nodes[0])
        builder.set_entry_point(entry_name)

        for i in range(len(nodes) - 1):
            cur_name = get_node_name(nodes[i])
            next_name = get_node_name(nodes[i + 1])
            builder.add_edge(cur_name, next_name)

        finish_name = get_node_name(nodes[-1])
        builder.set_finish_point(finish_name)

    @computed_field
    @property
    def graph_nodes(self) -> list[BaseGraphNode]:
        if self._graph_nodes:
            return self._graph_nodes
        self._graph_nodes = self._get_nodes()
        return self._graph_nodes

    def compile_graph(self) -> CompiledGraph:
        builder = StateGraph(self._get_state_type())
        builder.support_multiple_edges = True

        nodes = self.graph_nodes

        [node.join_graph(builder) for node in nodes]

        self._set_edges(builder)

        return builder.compile(checkpointer=MemorySaver())

    def _process_input(self, input: BaseModel) -> dict:
        if not input:
            return {}
        return self._base_model_to_typed_dict(input)

    def _base_model_to_typed_dict(self, input: BaseModel):
        input_dict = input.model_dump()
        for key, value in input.__dict__.items():
            if isinstance(value, BaseModel):
                input_dict[key] = value

        return input_dict

    async def _post_invoke_ret(self, state: dict) -> Optional[Any]:
        return state

    async def call(self, input: Input) -> Optional[Output]:
        ret = None
        try:
            graph = self.compile_graph()
            graph_input = self._process_input(input)
            graph_ret = await graph.ainvoke(graph_input,
                                            config=create_agent_runnable_config(
                                                max_concurrency=4,
                                                callbacks=[LLMLogCallbackHandler()])
                                            )
            ret = await self._post_invoke_ret(graph_ret)
        except Exception as e:
            logger.warning(f"{self.__class__.__name__} call: {e}", exc_info=True)
        return ret

    async def abatch(self, input_list: List[Input]) -> List[Output]:
        rets = []
        try:
            graph = self.compile_graph()
            inputs = [self._process_input(input) for input in input_list] if input_list is not None else []
            graph_rets = await graph.abatch(inputs, return_exceptions=True)
            for graph_ret in graph_rets:
                rets.append(await self._post_invoke_ret(graph_ret))
        except Exception as e:
            logger.warning(f"{self.__class__.__name__} abatch: {e}", exc_info=True)
        return rets

    async def astream_generator(self, input: Input = None) -> AsyncGenerator:
        try:
            graph = self.compile_graph()
            graph_input = self._process_input(input)
            ret = graph.astream(graph_input)
            async for item in ret:
                async for chunk in self._handel_astream_generator_ret(item):
                    yield chunk
        except Exception as e:
            logger.warning(f"{self.__class__.__name__} astream_generator: {e}", exc_info=True)

    async def _handel_astream_generator_ret(self, item):
        state: dict = (next(iter(item.values())))
        step = next(iter(item.keys()))
        nodes = self.graph_nodes
        chunk = item
        for node in nodes:
            match = False
            if isinstance(node, BaseGraphNode):
                match = node.__class__.node_name() == step
            if match:
                chunk = await node._stream_output(state)
                break
        if chunk:
            yield chunk


class EndGraphNode(BaseGraphNode):

    @classmethod
    def node_name(cls) -> str:
        return "end_node"

    async def _func(self, state: TypedDict):
        return state

    async def _stream_output(self, state: TypedDict, is_demo: bool = False):
        return "END"


async def recall_market_cap_coins(large_cap_million):
    params = {
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1
    }
    all_coins = []
    while True:
        response = requests.get(params=params)
        response.raise_for_status()
        data = response.json()
        if not data:
            break
        large_cap_coins = [coin for coin in data if coin.get("market_cap", 0) > large_cap_million]
        all_coins.extend(large_cap_coins)
        params["page"] += 1
    return all_coins


async def filter_coins_by_platform(coins):
    solana_coins = []
    for coin in coins:
        coin_id = coin["id"]
        platforms = {}.get("platforms", {})
        if "solana" in platforms:
            solana_coins.append({
                "id": coin_id,
                "name": coin["name"],
                "symbol": coin["symbol"],
                "solana_address": platforms["solana"]
            })
    return solana_coins


async def search_derivative_new_coins():
    params = {
        "type": "token"
    }
    headers = {"Authorization": ""}
    response = requests.get(headers=headers, params=params)
    response.raise_for_status()
    return response.json()


async def rank_coins(market_data):
    filtered = [token for token in market_data if 6000 <= token["market_cap"] <= 20000]
    sorted_tokens = sorted(filtered, key=lambda x: x["total_volume"], reverse=True)
    return sorted_tokens[:10]
