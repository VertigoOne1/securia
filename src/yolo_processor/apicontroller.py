import os, time, json, sys
from flask import jsonify, request, Flask
from envyaml import EnvYAML
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from datetime import datetime, timezone
from prometheus_client import make_wsgi_app
from pprint import pformat
from threading import Thread
from defroutes import health_bp
from logger import setup_custom_logger
import metrics

logger = setup_custom_logger(__name__)

config = EnvYAML('config.yml')

APP_NAME = config['general']['app_name']

app = Flask(__name__)
app.register_blueprint(health_bp)

#Prometheus metrics
if config["metrics"]["enabled"]:
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        f"/metrics": make_wsgi_app()
    })

class FlaskThread(Thread):
    def run(self):
        app.run(
            host='0.0.0.0',
            port=config['flask']['default_port'],
            debug=config['flask']['debug_enabled'],
            use_debugger=config['flask']['debug_enabled'],
            use_reloader=False)