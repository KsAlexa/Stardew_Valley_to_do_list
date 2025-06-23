class Task:
    def __init__(self, name: str, day_id: int, type: str, status: str, task_id: int = None):
        self.name = name
        self.day_id = day_id
        self.type = type
        self.status = status
        self.id = task_id

    def __eq__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return (
            self.id == other.id and
            self.name == other.name and
            self.day_id == other.day_id and
            self.type == other.type and
            self.status == other.status
        )
