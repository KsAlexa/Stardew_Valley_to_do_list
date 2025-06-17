from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse

from ..errors import *
from ..main import app


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request, exc):
    data = {'error': exc.message}
    return JSONResponse(content=data, status_code=404)

@app.exception_handler(InvalidTaskStateException)
async def not_found_exception_handler(request, exc):
    data = {'error': exc.message}
    return JSONResponse(content=data, status_code=400)
