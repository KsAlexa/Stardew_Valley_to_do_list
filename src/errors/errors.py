class NotFoundException(BaseException):
    def __init__(self, message: str):
        self.message = message

class InvalidStateException(BaseException):
    def __init__(self, message: str):
        self.message = message