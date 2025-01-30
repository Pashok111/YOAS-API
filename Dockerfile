###############
### BUILDER ###
###############

FROM python:3.13.1-alpine AS builder

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python3 -m venv $VIRTUAL_ENV

RUN pip install --upgrade pip

COPY ./requirements.txt .
RUN pip install -r requirements.txt


##############
### RUNNER ###
##############

FROM python:3.13.1-alpine AS runner

LABEL authors="Pashok11"

COPY --from=builder /opt/venv /opt/venv

ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV APP=/app
ENV DB_N_LOGS_FOLDER=$APP/db_n_logs
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE $PORT

RUN mkdir $APP
RUN mkdir $DB_N_LOGS_FOLDER
WORKDIR $APP

COPY ./*.env ./
COPY ./main.py ./
COPY ./api_versions/ ./api_versions/

ENTRYPOINT ["/bin/sh", "-c", \
            "fastapi run main.py \
            --host $HOST --port $PORT \
            >> $DB_N_LOGS_FOLDER/$(date +'%Y-%m-%d__%H-%M-%S%z').log"]