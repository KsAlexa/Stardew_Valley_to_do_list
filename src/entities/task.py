class Task:
    def __init__(self, name: str, day_id: int, type: str, status: str, task_id: int = None):
        self.name = name
        self.day_id = day_id
        self.type = type
        self.status = status
        self.id = task_id

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "day_id": self.day_id
        }