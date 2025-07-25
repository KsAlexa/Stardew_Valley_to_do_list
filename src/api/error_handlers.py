from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse, PlainTextResponse

from ..errors import *
from ..main import app


@app.exception_handler(InternalException)
async def internal_exception_handler(_, exc):
    print(str(exc))  # TODO: use logger
    data = {'error': 'Internal Error'}
    return JSONResponse(content=data, status_code=500)


@app.exception_handler(MultipleActiveDaysException)
async def multiple_active_days_exception_handler(_, exc):
    print(str(exc))
    data = {'error': 'Internal Error'}
    return JSONResponse(content=data, status_code=500)

@app.exception_handler(TaskNotFoundException)
async def task_not_found_exception_handler(_, exc):
    data = {'error': 'Task not found'}
    return JSONResponse(content=data, status_code=404)


@app.exception_handler(InvalidTaskStateException)
async def invalid_task_state_exception_handler(_, exc):
    data = {'error': exc.message}
    return JSONResponse(content=data, status_code=400)


@app.exception_handler(InvalidDayError)
async def invalid_day_error_handler(_, exc):
    data = {'error': exc.message}
    return JSONResponse(content=data, status_code=400)


@app.exception_handler(DuplicateDayException)
async def duplicate_day_exception_handler(_, exc):
    data = {'error': 'Day already exists'}
    return JSONResponse(content=data, status_code=409)


@app.exception_handler(DuplicateTaskNameException)
async def duplicate_task_name_exception_handler(_, exc):
    data = {'error': 'Task already exists'}
    return JSONResponse(content=data, status_code=409)