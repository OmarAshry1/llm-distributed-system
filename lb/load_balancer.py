class LoadBalancer:
    def __init__(self, workers):
        self.workers = workers
        self.index = 0

    def get_nexT_worker(self):
        worker = self.workers[self.index]
        self.index = (self.index + 1) % len(self.workers)
        return worker
    
    def dispatch(self, request):
        worker = self.get_next_worker()
        return worker.process(request)