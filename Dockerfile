FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

# Optional build argument for different environments
ARG ENV

RUN apt-get -y update && apt-get -y --no-install-recommends install \
        make gcc libc-dev libgeos-dev musl-dev libpq-dev libffi-dev

RUN pip install --upgrade pip && pip install pipenv==2021.5.29
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN if [ "$ENV" = "dev" ] || [ "$ENV" = "test" ]; then \
	     echo "Install all dependencies" && \
	     apt-get install -y --no-install-recommends git postgresql-client && \
	     pipenv install --system --deploy --ignore-pipfile --dev && \
         apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common && \
         curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add - && \
         apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main" && \
         apt-get update && apt-get install terraform; \
	else \
	     echo "Install production dependencies only" && \
	     pipenv install --system --deploy; \
	fi

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./app /app/app
COPY wait_for_postgres.sh /usr/local/bin/wait_for_postgres.sh
RUN chmod +x /usr/local/bin/wait_for_postgres.sh