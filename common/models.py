from dataclasses import dataclass

@dataclass
class Request:
    id: int
    query: str

@dataclass
class Response:
    id: int
    result: str
    latency: float