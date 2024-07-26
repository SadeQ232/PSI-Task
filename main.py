from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import platform
import logging

from app.metrics import collect_metrics, registry, collect_windows_specific_metrics
from app.logging_setup import setup_logging

setup_logging()

app = FastAPI(title='septian_exporter', version='0.1.0', debug=False, description='Monitoring Script for Windows or Linux OS using python FastAPI', docs_url=None)


@app.get('/')
async def health_check():
    return {"Monitoring Script for Windows or Linux OS": "Running"}


@app.get('/metrics')
async def metrics(request: Request):
    logging.info(f"Received request for /metrics from {request.client.host}")
    collect_metrics()

    if platform.system() == 'Windows':
        collect_windows_specific_metrics()

    data = generate_latest(registry)
    return PlainTextResponse(data, media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    logging.info("Starting metrics collector application")
    import uvicorn

    try:
        uvicorn.run('main:app', host='localhost', port=8000)
        logging.info("Started Prometheus HTTP server on port 8000")
    except Exception as e:
        logging.critical(f"Critical error: {e}")
    finally:
        logging.info("Shutting down metrics collector application")
