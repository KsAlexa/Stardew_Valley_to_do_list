from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse, PlainTextResponse

from ..errors import *
from ..main import app


@app.exception_handler(InternalException)
async def internal_exception_handler(_, exc):
    print(str(exc))  # TODO: use logger
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
