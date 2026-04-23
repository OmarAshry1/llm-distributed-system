class Scheduler:
    def __init__(self, workers):
        self.workers = workers

    def handle_request(self, request):
        print(f"[Scheduler] Dispatching request {request.id}")
        response = self.lb.dispatch(request)
        return response