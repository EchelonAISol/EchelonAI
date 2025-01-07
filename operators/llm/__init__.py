import logging
from abc import abstractmethod, ABC
from typing import TypeVar, Optional, AsyncGenerator

import simplejson
from pydantic import BaseModel, Field
from pyecharts.charts.base import Base, default
from pyecharts.commons import utils

from echelon.chains.chain_manager import create_simple_chain

logger = logging.getLogger(__name__)

BaseModelInput = TypeVar("BaseModelInput", bound=BaseModel, contravariant=True)
BaseModelOutput = TypeVar("BaseModelOutput", bound=BaseModel, contravariant=True)
LLmOutput = TypeVar("LLmOutput", covariant=True)


class LLMPredictOp(ABC, BaseModel):
    llm_output_model: type[BaseModel] | str = str
    default_human_prompt: str = "",

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    async def predict(self, input: BaseModelInput) -> Optional[LLmOutput]:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, input: BaseModelInput) -> AsyncGenerator:
        raise NotImplementedError

    async def _stream_default(self, input: BaseModelInput) -> AsyncGenerator:
        processed_input = await self._pre_process(input)
        async for chunk in self._llm_stream(processed_input):
            yield chunk

    async def _predict_default(self, input: BaseModelInput) -> Optional[LLmOutput]:
        try:
            processed_input = await self._pre_process(input)
            llm_output = await self._llm(processed_input)
            return await self._post_process(input, llm_output)
        except Exception as e:
            logger.error(f"_predict_default: {e}")
            return None

    async def _pre_process(self, input: BaseModelInput) -> BaseModelInput:
        return input

    async def _llm(self, input: BaseModelInput) -> Optional[LLmOutput]:

        input_dict = input.model_dump()

        chain = create_simple_chain(default_human_prompt=self.default_human_prompt,
                                    llm_output_model=self.llm_output_model,
                                    image_url=input_dict.get("image_url", None), )
        return await chain.ainvoke(input_dict)

    async def _llm_stream(self, input: BaseModelInput) -> AsyncGenerator:
        input_dict = input.model_dump()
        chain = create_simple_chain(default_human_prompt=self.default_human_prompt,
                                    image_url=input_dict.get("image_url", None), )
        async for chunk in chain.astream(input_dict):
            yield chunk

    async def _post_process(self, input: BaseModelInput, llm_output: Optional[LLmOutput]) -> Optional[LLmOutput]:
        return llm_output


class UserInputReq(BaseModel):
    """
    UserInput
    """
    user_input: str


class EChartOpReq(BaseModel):
    text: str = Field(description="文本内容")


class EChartOpResp(BaseModel):
    chart: Base = None
    options: str = None

    class Config:
        arbitrary_types_allowed = True


class EChartOp(LLMPredictOp, ABC):

    async def predict(self, input: EChartOpReq) -> Optional[EChartOpResp]:
        return await self._predict_default(input)

    async def stream(self, input: EChartOpReq) -> AsyncGenerator:
        raise NotImplementedError

    async def _post_process(self, input: BaseModelInput, llm_output: Optional[LLmOutput]) -> Optional[
        EChartOpResp]:
        chart = await self._to_chart(input, llm_output)
        return await self._to_resp(chart, input)

    @abstractmethod
    async def _to_chart(self, input: EChartOpReq, llm_output: Optional[LLmOutput]) -> Optional[Base]:
        pass

    async def _to_resp(self, chart: Optional[Base], input: EChartOpReq) -> Optional[EChartOpResp]:
        if not isinstance(chart, Base):
            return None

        options = utils.replace_placeholder(
            simplejson.dumps(chart.get_options(), indent=None, default=default, ignore_nan=True, ensure_ascii=False)
        )

        chart.dump_options()

        return EChartOpResp(
            chart=chart,
            options=options,
        )
