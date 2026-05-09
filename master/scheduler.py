from common.quiet import dprint


class Scheduler:
    def __init__(self, load_balancer):
        self.lb = load_balancer

    def handle_request(self, request):
        dprint(f"[Scheduler] Dispatching request {request.id}")
        return self.lb.dispatch(request)

    def route_request(self, request):
        return self.handle_request(request)
