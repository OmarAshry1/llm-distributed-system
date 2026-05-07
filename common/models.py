from dataclasses import dataclass

class Request:
    def __init__(self, id, query, client_id):
        self.id = id
        self.query = query
        self.client_id = client_id

@dataclass
class Response:
    id: str
    result: str
    latency: float
    worker_id: int | None = None
    success: bool = True
    error: str | None = None
    attempts: int = 1
