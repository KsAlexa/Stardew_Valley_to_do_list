from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse, PlainTextResponse

from ..errors import *

_app = None

def get_app():
    if _app is None:
        from ..main import app
        return app
    return _app


@get_app().exception_handler(InternalException)
async def internal_exception_handler(_, exc):
    print(str(exc))  # TODO: use logger
    data = {'error': 'Internal Error'}
    return JSONResponse(content=data, status_code=500)


@get_app().exception_handler(MultipleActiveDaysException)
async def multiple_active_days_exception_handler(_, exc):
    print(str(exc))
    data = {'error': 'Internal Error'}
    return JSONResponse(content=data, status_code=500)

@get_app().exception_handler(TaskNotFoundException)
async def task_not_found_exception_handler(_, exc):
    data = {'error': 'Task not found'}
    return JSONResponse(content=data, status_code=404)


@get_app().exception_handler(InvalidTaskStateException)
async def invalid_task_state_exception_handler(_, exc):
    data = {'error': exc.message}
    return JSONResponse(content=data, status_code=400)


@get_app().exception_handler(InvalidDayError)
async def invalid_day_error_handler(_, exc):
    data = {'error': exc.message}
    return JSONResponse(content=data, status_code=400)


@get_app().exception_handler(DuplicateDayException)
async def duplicate_day_exception_handler(_, exc):
    data = {'error': 'Day already exists'}
    return JSONResponse(content=data, status_code=409)


@get_app().exception_handler(DuplicateTaskNameException)
async def duplicate_task_name_exception_handler(_, exc):
    data = {'error': exc.message}
    return JSONResponse(content=data, status_code=409)