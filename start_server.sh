#!/bin/bash
source ./.env
uvicorn app.main:app --reload --host $IP --port $PORT --ws websockets