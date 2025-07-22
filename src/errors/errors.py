class  InternalException(Exception):
    def __init__(self, message: str):
        self.message = message


class TaskNotFoundException(Exception):
    def __init__(self, message: str):
        self.message = message

class TaskNotInActiveDayError(Exception):
    def __init__(self, message: str):
        self.message = message

class InvalidTaskStateException(Exception):
    def __init__(self, message: str):
        self.message = message

class DuplicateTaskNameException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class DuplicateDayException(Exception):
    def __init__(self, message: str):
        self.message = message

class MultipleActiveDaysException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class InvalidDayError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
