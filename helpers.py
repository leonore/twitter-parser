import queue

class SetQueue(queue.Queue):

    def put(self, item, block=True, timeout=None):
        if item not in self.queue: # fix join bug
            queue.Queue.put(self, item, block, timeout)

    def _init(self, maxsize):
        self.queue = set()

    def _put(self, item):
        self.queue.add(item)

    def _get(self):
        return self.queue.pop()
