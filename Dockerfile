#FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7
FROM cmgg/uvicorn-gunicorn-docker:python3.8-alpine3.11

RUN apk update && \
    apk add --virtual .build-deps gcc  musl-dev postgresql-dev

RUN pip install mercantile databases[postgresql]

COPY ./app /app

RUN apk del .build-deps gcc libc-dev make