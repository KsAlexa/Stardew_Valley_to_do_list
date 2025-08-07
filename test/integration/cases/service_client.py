from fastapi.testclient import TestClient
from src.api.handlers_models import *

class ServiceClient:
    def __init__(self, client: TestClient):
        self.client = client

    def get_current_state(self) -> CurrentStateResponse:
        response = self.client.get("/day/current")
        response.raise_for_status()
        return CurrentStateResponse.model_validate(response.json())

    def set_current_day(self, request: SetCurrentDayRequest) -> CurrentStateResponse:
        response = self.client.put("/day/current", json=request.model_dump())
        response.raise_for_status()
        return CurrentStateResponse.model_validate(response.json())

    def set_next_day(self) -> CurrentStateResponse:
        response = self.client.post("/day/next")
        response.raise_for_status()
        return CurrentStateResponse.model_validate(response.json())

    def create_task(self, request: TaskNameRequest) -> TaskResponse:
        if isinstance(request, BaseModel):
            payload = request.model_dump()
        else:
            payload = request
        response = self.client.post("/task/", json=payload)
        response.raise_for_status()
        return TaskResponse.model_validate(response.json())

    def rename_task(self, task_id: int, request: TaskNameRequest) -> TaskResponse:
        if isinstance(request, BaseModel):
            payload = request.model_dump()
        else:
            payload = request
        response = self.client.patch(f"/task/{task_id}/rename", json=payload)
        response.raise_for_status()
        return TaskResponse.model_validate(response.json())

    def complete_task(self, task_id: int) -> TaskResponse:
        response = self.client.patch(f"/task/{task_id}/complete")
        response.raise_for_status()
        return TaskResponse.model_validate(response.json())

    def activate_task(self, task_id: int) -> TaskResponse:
        response = self.client.patch(f"/task/{task_id}/active")
        response.raise_for_status()
        return TaskResponse.model_validate(response.json())

    def make_task_daily(self, task_id: int) -> TaskResponse:
        response = self.client.patch(f"/task/{task_id}/daily")
        response.raise_for_status()
        return TaskResponse.model_validate(response.json())
    
    def make_task_one_time(self, task_id: int) -> TaskResponse:
        response = self.client.patch(f"/task/{task_id}/one_time")
        response.raise_for_status()
        return TaskResponse.model_validate(response.json())
