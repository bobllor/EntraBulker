from typing import Literal, TypedDict, Any

type LogLevel = Literal["debug", "info", "warn", "critical"]

class LogObject(TypedDict):
    level: LogLevel
    component: str
    msg: str
    data: Any | None