from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.metrics import collect_metrics, registry
from app.logging_setup import setup_logging

setup_logging()

app = FastAPI()

@app.get('/metrics')
async def metrics(request: Request):
    # Log HTTP request
    import logging
    logging.info(f"Received request for /metrics from {request.client.host}")
    collect_metrics()
    data = generate_latest(registry)
    return PlainTextResponse(data, media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import logging
    logging.info("Starting metrics collector application")
    import uvicorn
    try:
        uvicorn.run(app, host='localhost', port=8000)
        logging.info("Started Prometheus HTTP server on port 8000")
    except Exception as e:
        logging.critical(f"Critical error: {e}")
    finally:
        logging.info("Shutting down metrics collector application")
