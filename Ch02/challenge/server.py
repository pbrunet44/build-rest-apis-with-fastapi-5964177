"""Write an /info handler that will return a JSON object with:

- version: string, say "0.1.0"
- time: the current time in ISO format
- user: The user running the application (hint: USER environment variable)
"""
from fastapi import FastAPI
from datetime import datetime
from os import getenv

app = FastAPI()


@app.get('/info')
def info():
    return {
        'version': '0.1.0',
        'time': datetime.now().isoformat(),
        'user': getenv('USER')
    }
