class InternalException(Exception):
    def __init__(self, message: str):
        self.message = message


class TaskNotFoundException(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidTaskStateException(Exception):
    def __init__(self, message: str):
        self.message = message
