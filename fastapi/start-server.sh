#!/usr/bin/env bash
export AAR_ENV=${AAR_ENV:-local}
uvicorn app.main:app --host 0.0.0.0 --port 9223 --reload
