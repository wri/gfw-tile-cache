FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install mercantile asyncpg

COPY ./app /app
