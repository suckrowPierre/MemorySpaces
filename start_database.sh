#!/bin/bash
source ./.env
uvicorn app.db:app --host $IP_DB --port $PORT_DB