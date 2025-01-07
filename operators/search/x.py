import logging
from typing import Optional, List

import aiohttp
from langchain_core.documents import Document
from pydantic import BaseModel

from echelon.common.codec import jsondumps
from echelon.operators.search import SearchOp, get_x_token, ban_token

logger = logging.getLogger(__name__)


def calculate_rank(public_metrics: dict) -> float:
    weights = {
        'retweet_count': 10,
        'reply_count': 5,
        'like_count': 5,
        'quote_count': 3,
        'bookmark_count': 2,
        'impression_count': 1
    }

    rank = 0
    for key, weight in weights.items():
        rank += public_metrics.get(key, 0) * weight

    return rank


def sort_documents(docs: List[Document]) -> List[Document]:
    docs.sort(key=lambda doc: doc.metadata.get("rank", 0), reverse=True)
    return docs


def group_and_sort_documents(docs: List[Document]) -> List[Document]:
    if not docs:
        return []

    blue_docs = [doc for doc in docs if doc.metadata.get("verified_type") == "blue"]
    other_docs = [doc for doc in docs if doc.metadata.get("verified_type") != "blue"]

    sorted_blue_docs = sort_documents(blue_docs)
    if len(sorted_blue_docs) > 10:
        combined_docs = sorted_blue_docs
        result_docs = sorted_blue_docs[:10]
    else:
        sorted_other_docs = sort_documents(other_docs)
        combined_docs = sorted_blue_docs + sorted_other_docs
        result_docs = combined_docs[:10]

    has_media_image_urls = False
    for doc in result_docs:
        if doc.metadata.get("media_image_urls", None):
            has_media_image_urls = True
            break

    if not has_media_image_urls:
        for doc in combined_docs:
            media_image_urls = doc.metadata.get("media_image_urls", [])
            if media_image_urls and len(media_image_urls) > 0:
                result_docs = result_docs[:-1] + [doc]

    return result_docs


class XSearchReq(BaseModel):
    query: str
    max_results: int = 10


class Media(BaseModel):
    type: str
    preview_image_url: str


class XSearchOp(SearchOp):

    async def search(self, input: XSearchReq) -> Optional[List[Document | Media]]:
        x_token = get_x_token()
        headers = {
            'Authorization': f'Bearer {x_token}'
        }

        # now = datetime.now(pytz.utc)
        # six_hours_ago = now - timedelta(hours=24)
        # start_time = six_hours_ago.isoformat()

        search_url = "https://api.twitter.com/2/tweets/search/recent"
        query_params = {
            # 'start_time': start_time,
            'query': input.query,
            'max_results': input.max_results,
            'tweet.fields': 'created_at,public_metrics,author_id',
            'expansions': 'attachments.media_keys,author_id',
            'media.fields': 'url,preview_image_url',
            'user.fields': 'name,profile_image_url,verified,verified_type',
        }

        ret = []

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers, params=query_params) as response:
                if response.status == 429:
                    ban_token(x_token)
                    logger.warning(
                        f"Rate limit exceeded. X-Rate-Limit-Reset: {response.headers.get('X-Rate-Limit-Reset')}")
                    return []
                response.raise_for_status()
                tweets = await response.json()
                logger.info(f"Query {input.query} Got tweets: {jsondumps(tweets)})")

                users_dict = {}
                if tweets.get('includes', None):
                    includes = tweets.get('includes')
                    users = includes.get('users', [])
                    for user in users:
                        users_dict[user["id"]] = user

                media_dict = {}
                if tweets.get('includes', None):
                    includes = tweets.get('includes')
                    medias = includes.get('media', [])
                    for media in medias:
                        media_dict[media['media_key']] = media

                if tweets.get('data', None):
                    for tweet in tweets['data']:
                        author_info = users_dict.get(tweet.get("author_id", ""), {})

                        media_image_urls = []
                        media_keys = tweet.get('attachments', {}).get('media_keys', [])
                        for media_key in media_keys:
                            media_info = media_dict.get(media_key, {})
                            media_image_url = media_info.get('preview_image_url', "")
                            if media_image_url:
                                media_image_urls.append(media_image_url)
                            else:
                                media_url = media_info.get('url', "")
                                if media_url:
                                    media_image_urls.append(media_url)

                        m_username = author_info.get("username", "")
                        m_x_id = tweet.get("id", "")

                        metadata = {
                            "content": tweet["text"],
                            "created_at": tweet.get("created_at", ""),
                            "query": input.query,
                            "site": "x",
                            "verified": author_info.get("verified", False),
                            "username": m_username,
                            "profile_image_url": author_info.get("profile_image_url", ""),
                            "verified_type": author_info.get("verified_type", ""),
                            "public_metrics": tweet.get("public_metrics", {}),
                            "rank": calculate_rank(tweet.get("public_metrics", {})),
                            "media_image_urls": media_image_urls,
                            "x_id": m_x_id,
                            "x_post_url": f"https://x.com/{m_username}/status/{m_x_id}"
                        }

                        doc = Document(
                            page_content=tweet["text"],
                            metadata=metadata,
                        )
                        ret.append(doc)

                ret = group_and_sort_documents(ret)

                if tweets.get('includes', None):
                    includes = tweets.get('includes')
                    media = includes.get('media', [])
                    for media in media:
                        media_type = media.get("type", "none")

                        media_preview_image_url = media.get("preview_image_url", None)
                        if media_preview_image_url:
                            ret.append(Media(type=media_type, preview_image_url=media_preview_image_url))
                        else:
                            media_url = media.get("url", None)
                            if media_url:
                                ret.append(Media(type=media_type, preview_image_url=media_url))

        return ret
