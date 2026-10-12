"""Make this server production ready:
- Plug security holes
- Add some logging
- Add some metrics
"""

import csv
import math
import logging
from datetime import datetime
from io import StringIO
from time import perf_counter
from http import HTTPStatus

from fastapi import FastAPI, Request, HTTPException


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S',
)

app = FastAPI()
log = logging.getLogger('uvicorn')


lat_km = 92
lng_km = 111

MAX_FILE_SIZE = 5 * (1 << 20)


def distance(lat1, lng1, lat2, lng2):
    """Return euclidean distance (in kilometers) between two coordinates.

    >>> distance(0, 0, 1, 1)
    144.1700384962146
    """

    delta_lat = (lat1 - lat2) * lat_km
    delta_lng = (lng1 - lng2) * lng_km
    dist = math.hypot(delta_lat, delta_lng)
    log.info('euclidean distance in km between (%s, %s) and (%s, %s) is %.2f',
             lat1, lng1, lat2, lng2, dist)
    return dist


def parse_csv(fp):
    """Parse CSV, returns tuple of:
    - number of samples
    - total distance
    - average speed in km/h
    """
    reader = csv.DictReader(fp)
    start_time = end_time = None
    prev_lat = prev_lng = None
    count = total_distance = 0

    for row in reader:
        count += 1
        time = datetime.fromisoformat(row['time'])
        # Rows are in chronological order
        if start_time is None:
            start_time = time
        else:
            end_time = time

        lat, lng = float(row['lat']), float(row['lng'])
        if prev_lat:
            total_distance += distance(lat, lng, prev_lat, prev_lng)
        prev_lat, prev_lng = lat, lng

    duration_hours = (end_time - start_time).total_seconds() / (60 * 60)
    speed = total_distance / duration_hours

    log.info('parsed csv, found %s samples, total distance %.2f, avg speed %.2f km/h',
             count, total_distance, speed)
    return count, total_distance, speed


@app.post('/run')
async def run_stats(request: Request):
    start = perf_counter()
    mime_type = request.headers['content-type']
    file_size = int(request.headers['Content-Length'])
    if mime_type != 'text/csv':
        log.error('bad format: %s', mime_type)
        raise HTTPException(HTTPStatus.NOT_ACCEPTABLE,
                            detail='only csv files accepted')

    if file_size > MAX_FILE_SIZE:
        log.error('file size too large')
        raise HTTPException(
            HTTPStatus.REQUEST_ENTITY_TOO_LARGE, detail='file too large')

    data = await request.body()
    fp = StringIO(data.decode())
    count, distance, speed = parse_csv(fp)
    out = {
        'count': count,
        'distance': distance,
        'speed': speed,
    }
    duration = perf_counter() - start
    log.info(
        '[metric:call.duration] %s %s - %.2fs',
        request.method,
        request.url,
        duration,
    )
    return out
