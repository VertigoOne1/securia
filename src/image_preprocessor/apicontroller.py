import uvicorn
from fastapi import FastAPI, status
from pydantic import BaseModel
from prometheus_client import make_asgi_app
from envyaml import EnvYAML
from logger import setup_custom_logger
import threading
import signal
import sys

logger = setup_custom_logger(__name__)

config = EnvYAML('config.yml')

APP_NAME = config['general']['app_name']

app = FastAPI()
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

def start_api_server():
    uvconfig = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=config['api']['default_port'],
        log_level=config['api']['debug_level']
    )
    server = uvicorn.Server(uvconfig)

    def run_server():
        server.run()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    def signal_handler(signum, frame):
        print("Received shutdown signal. Stopping server...")
        server.should_exit = True
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            thread.join(timeout=1.0)
            if not thread.is_alive():
                break
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Stopping server...")
        server.should_exit = True
        sys.exit(0)

@app.get("/")
def root():
    return {"message": "SecurIA - Collector Simulator"}

class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"

@app.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health() -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on. This endpoint can primarily be used Docker
    to ensure a robust container orchestration and management is in place. Other
    services which rely on proper functioning of the API service will not deploy if this
    endpoint returns any other HTTP status code except 200 (OK).
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(status="OK")