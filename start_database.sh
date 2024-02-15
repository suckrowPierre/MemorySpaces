#!/bin/bash
source ./.env
uvicorn db.db:app --host $IP_DB --port $PORT_DB