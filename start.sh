#!/bin/bash
DB_N_LOGS_FOLDER="${DB_N_LOGS_FOLDER:-db_n_logs}"
mkdir -p "$DB_N_LOGS_FOLDER"
nohup fastapi run main.py --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" >> "$DB_N_LOGS_FOLDER/$(date +'%Y-%m-%d__%H-%M-%S%z').log"