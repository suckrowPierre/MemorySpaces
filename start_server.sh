#!/bin/bash
source ./.env
uvicorn app.main:app --host $IP --port $PORT --ws websockets