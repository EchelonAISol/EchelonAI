from typing import Optional

import aiohttp
from langchain_community.utilities import SearchApiAPIWrapper
from langchain_core.documents import Document
from pydantic import BaseModel

from echelon.common.config import SETTINGS
from echelon.operators.search import SearchOp


class SearchApiReq(BaseModel):
    query: str


class SearchApiOp(SearchOp):

    async def search(self, input: SearchApiReq) -> Optional[Document]:
        try:
            ret = await SearchApiAPIWrapper(searchapi_api_key=SETTINGS.SEARCHAPI_API_KEY).arun(query=input.query)
            if ret:
                metadata = {
                    "query": input.query,
                    "site": "google",
                }
                doc = Document(
                    page_content=ret,
                    metadata=metadata,
                )
                return doc
        except aiohttp.ClientResponseError as e:
            pass
        return None
        # metadata = {
        #     "created_at": tweet.get("created_at", ""),
        #     "query": input.query,
        #     "site": "x"
        # }
        # doc = Document(
        #     page_content=tweet["text"],
        #     metadata=metadata,
        # )
        # ret.append(doc)

        return ret
