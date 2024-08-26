from __future__ import absolute_import
import threading


thread_locals = threading.local()


def push_request(request):
    ''' pushes a request onto the stack '''
    if not getattr(thread_locals, "request", None):
        thread_locals.requests = []
    thread_locals.requests.append(request)


def pop_request(request):
    ''' pops the current request from the stack '''
    thread_locals.requests.pop()


def get_request():
    ''' returns the current request '''
    requests = getattr(thread_locals, "requests", [])
    if requests:
        return requests[-1]


class RequestMiddleware(object):
    """
    Stores the request in threadlocals
    """
    def process_request(self, request):
        push_request(request)

    def process_response(self, request, response):
        pop_request(request)
        return response