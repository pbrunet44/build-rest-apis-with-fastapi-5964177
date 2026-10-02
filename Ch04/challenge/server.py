"""Write a handler to query logs.
The handler accept the following query parameters:
- offset (default to 0)
- count (default to 100)

    GET /logs?offset=10&count=20

If should use db.query_logs to get the logs and return them as a JSON response in the
following format:
{
    "count": <count>,
    "offset": <offset>,
    "logs": [
        {"level": "INFO", "time": "2024-01-01T00:00:00", "message": "Log message #0000"},
        {"level": "WARNING", "time": "2024-01-01T00:00:12.345000", "message": "Log message #0001"},
        ...
    ]
}

If the HTTP header `Accept` is set to `text/csv`, the handler should return the logs in
CSV format:
    level,time,message
    INFO,2024-01-01T00:00:00,Log message #0000
    WARNING,2024-01-01T00:00:12.345000,Log message #0001
    ...

If no logs matches the query, return a 404 (NOT_FOUND) response.
Don't forget to validate everything.

"""
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel

import db

import csv
from http import HTTPStatus
from io import StringIO
from datetime import datetime

app = FastAPI()


class Log(BaseModel):
    level: str
    time: datetime
    message: str


class LogsResponse(BaseModel):
    count: int
    offset: int
    logs: list[Log]


@app.get('/logs')
def get_logs(req: Request, offset: int = 0, count: int = 100):
    if count < 1 or offset < 0:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail='count must be positive integer, offset must be non-negative integer')
    logs = db.query_logs(offset, count)
    if not logs:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='logs not found')
    mime_type = req.headers.get('Accept')
    if mime_type in {'application/json', '*/*', None}:
        return LogsResponse(count=count, offset=offset, logs=[Log(**log) for log in logs])
    elif mime_type == 'text/csv':
        return csv_response(logs)
    else:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail='Accept header must be application/json (default) or text/csv')


def csv_response(logs: list[dict]):
    io = StringIO()
    writer = csv.DictWriter(io, fieldnames=['level', 'time', 'message'])
    writer.writeheader()
    for log in logs:
        writer.writerow({
            'level': log['level'],
            'time': log['time'].isoformat(),
            'message': log['message']
        })
    return Response(content=io.getvalue(), media_type='text/csv')
