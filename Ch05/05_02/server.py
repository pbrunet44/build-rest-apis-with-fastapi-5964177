import logging
from datetime import datetime, timedelta
from time import perf_counter

from fastapi import FastAPI, Request
import uvicorn

import db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S',
)

app = FastAPI()
log = logging.getLogger('uvicorn')


@app.get('/posts/{login}')
def get_posts(login: str, since: str = None):
    if since:
        since = datetime.strptime(since, '%Y%m%d')
    else:
        since = datetime.now() - timedelta(days=7)
        # Round to day
        since = datetime(since.year, since.month, since.day)

    log.info('get posts for %s since %s', login, since)
    posts = db.query_posts(login, since)
    return posts


@app.middleware('http')
async def timing(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    duration = perf_counter() - start
    log.info(
        '[metric:call.duration] %s %s %d - %.2fs',
        request.method,
        request.url,
        response.status_code,
        duration,
    )
    return response
