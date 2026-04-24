class LoadBalancer:
    def __init__(self, workers):
        self.workers = workers
        self.index = 0
        self.session_map = {}  # client_id → worker

    def get_next_worker(self):
        worker = self.workers[self.index]
        self.index = (self.index + 1) % len(self.workers)
        return worker

    def dispatch(self, request):
        client_id = request.client_id

        # el logic for sticky memory session
        if client_id in self.session_map:
            worker = self.session_map[client_id]
        else:
            worker = self.get_next_worker()
            self.session_map[client_id] = worker

        print(f"[LB] Client {client_id} → Worker {worker.id}")

        return worker.process(request)