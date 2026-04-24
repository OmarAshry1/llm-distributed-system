from dataclasses import dataclass

class Request:
    def __init__(self, id, query, client_id):
        self.id = id
        self.query = query
        self.client_id = client_id

@dataclass
class Response:
    id: int
    result: str
    latency: float