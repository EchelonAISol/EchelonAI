from typing import Any

from orjson import orjson


def jsondumps(obj: Any) -> str:
    return orjson.dumps(obj, option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY).decode('utf-8')


def jsonloads(obj: Any) -> dict:
    return orjson.loads(obj)
