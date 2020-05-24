FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN apt-get -y update&& apt-get -y install \
        make gcc libc-dev libgeos-dev musl-dev libpq-dev libffi-dev

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./app /app/app
