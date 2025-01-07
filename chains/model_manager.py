from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from echelon.chains.log_callback import LLMLogCallbackHandler
from echelon.common.config import SETTINGS


def get_chat_llm_model() -> BaseChatModel:
    # TODO
    model_name = "gpt-4o-2024-08-06"
    temperature = 0.01
    return ChatOpenAI(model_name=model_name,
                      openai_api_key=SETTINGS.OPENAI_API_KEY,
                      temperature=temperature,
                      callbacks=[LLMLogCallbackHandler()])
