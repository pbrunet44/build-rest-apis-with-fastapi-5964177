from fastapi import FastAPI

app = FastAPI()


@app.get('/health')
def health():
    return {'errors': None}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app)
