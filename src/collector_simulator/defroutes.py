#!/bin/python3

import json, os
from flask import Flask, Blueprint
from envyaml import EnvYAML

config = EnvYAML('config.yml')

APP_NAME = config['general']['app_name']

health_bp = Blueprint('health_bp', __name__)

@health_bp.route("/healthz")
def health_act():
    d = {}
    d["status"] = "UP"
    return json.dumps(d)