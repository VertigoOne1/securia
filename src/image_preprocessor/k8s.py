#!/usr/bin/env python3

# This is the main loop and functions to check internal cluster certs
# Sites are SSL checked, and the result of the analysis, sent to a prometheus exporter

from curses.ascii import isdigit
import sys
sys.path.append(r'./modules')

from envyaml import EnvYAML
import json, requests, socket
from time import sleep
import kubernetes
import os, fnmatch, traceback
import base64
from pprint import pformat
import urllib3
from time import sleep
import time, datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import logger, metrics
import rabbitmq

logger = logger.setup_custom_logger(__name__)

config = EnvYAML('config.yml')

def k8s_connection():
    if config["kubernetes"]["in_cluster"]:
        config.load_incluster_config()
    else:
        kubernetes.config.load_kube_config(config["kubernetes"]["kubeconfig_path"])
    v1 = kubernetes.client.CoreV1Api()
    return v1

def get_namespaces(k8s_con):
    namespaces = k8s_con.list_namespace()
    return namespaces

def k8s_filter_secrets(k8s_con, namespace, secret_prefix):
    print(f"Filtering secrets starting with - {secret_prefix} in namespace - {namespace}")
    secrets = k8s_con.list_namespaced_secret(namespace)
    # Filter secrets that start with the given prefix
    matching_secrets = {
        secret.metadata.name: secret.data
        for secret in secrets.items
        if secret.metadata.name.startswith(secret_prefix)
    }

    if matching_secrets:
        # logger.debug(f"{matching_secrets}")
        return matching_secrets
    else:
        return {}

def collect_rabbitmq_details(k8s_con, namespaces, secret_filter):
    rabbitmq_info = {}
    for ns in namespaces.items:
        if ns.metadata.name.startswith("prod-"):
            try:
                matched_secrets = k8s_filter_secrets(k8s_con, ns.metadata.name, secret_filter)
                logger.debug(f"Matched - {matched_secrets}")
                for secret_name, secret_data in matched_secrets.items():
                    if 'appsettings.json' in secret_data:
                        # Decode the base64 encoded appsettings.json
                        appsettings_json = base64.b64decode(secret_data['appsettings.json']).decode('utf-8')
                        # Parse the JSON
                        appsettings = json.loads(appsettings_json)
                        logger.debug(f"{appsettings}")
                        # Extract
                        rabbitmq_info["tenant_id"] = appsettings["GlobalOptions"]["TenantId"]
                        rabbitmq_info["rabbitmq_host"] = appsettings["RedQueueBrokerOptions"]["PublicQueueDns"][0]
                        rabbitmq_info["rabbitmq_vhost"] = appsettings["RedQueueBrokerOptions"]["VirtualHost"]["Name"]
                        rabbitmq_info["rabbitmq_user"] = appsettings["RedQueueBrokerOptions"]["AdminUser"]
                        rabbitmq_info["rabbitmq_pass"] = appsettings["RedQueueBrokerOptions"]["AdminPassword"]
                        logger.debug(f"{rabbitmq_info}")
            except kubernetes.client.exceptions.ApiException as e:
                if e.status != 404:  # Ignore 404 (Not Found) errors
                    logger.error(f"Error retrieving secret from namespace {ns.metadata.name}: {e}")
    return rabbitmq_info

# Using serviceaccount and internal k8s api directly
def setupKubernetesConnection():
    # APISERVER=https://kubernetes.default.svc
    # # Path to ServiceAccount token
    # SERVICEACCOUNT=/var/run/secrets/kubernetes.io/serviceaccount
    # # Read this Pod's namespace
    # NAMESPACE=$(cat ${SERVICEACCOUNT}/namespace)
    # # Read the ServiceAccount bearer token
    # TOKEN=$(cat ${SERVICEACCOUNT}/token)
    # # Reference the internal certificate authority (CA)
    # CACERT=${SERVICEACCOUNT}/ca.crt
    # Explore the API with TOKEN
    # curl --cacert ${CACERT} --header "Authorization: Bearer ${TOKEN}" -X GET ${APISERVER}/api
    con_data = {}
    if config['kubernetes']['enabled']:
        logger.debug("Checking internal kubernetes api server")
        logger.debug("Make sure your service account can access the API!")
        try:
            con_data['api_server'] = "https://kubernetes.default.svc/api"
            t = open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r")
            con_data['token'] = t.read()
            t.close()
            c = open("/var/run/secrets/kubernetes.io/serviceaccount/ca.crt", "r")
            con_data['ca_cert'] = c.read()
            c.close()
            con_data['verify_ca'] = config['kubernetes']['verify_k8s_api_ca']
        except:
            logger.warn("Exception fetching kubernetes api information from pod /var/run")
            logger.error(traceback.format_exc())
        return con_data

def testKubernetesConnection(con_data):
    endpoint = con_data['api_server']
    try:
        response = requests.get(endpoint, auth=BearerAuth(con_data['token']), verify=con_data['verify_ca'])
        logger.debug(response.json())
        resp = response.json()
        result = {}
        if response.status_code == 401:
            logger.error("Issue with authentication/authorisation")
            logger.error("Check token")
            logger.error(response.json())
            result['success'] = False
            return result
        elif response.status_code == 200:
            # logger.debug("good response code")
            if "serverAddressByClientCIDRs" in resp:
                # logger.debug("Got suitable response")
                result['success'] = True
                return result
            else:
                result['success'] = False
                return result
        else:
            result['success'] = False
            return result
    except Exception:
        logger.error(traceback.format_exc())
        logger.error("Exception testing kubernetes connection")
        result = {}
        result['success'] = False
        return result

def k8sgetAllNamespaces(con_data):
    endpoint = con_data['api_server']
    url = "/v1/namespaces"
    try:
        response = requests.get(f"{endpoint}{url}", auth=BearerAuth(con_data['token']), verify=con_data['verify_ca'])
        # logger.debug(response.json())
        resp = response.json()
        result = {}
        if response.status_code == 200:
            # logger.debug("good response code")
            if "items" in resp:
                namespaces = []
                # logger.debug("Got suitable response")
                for item in resp['items']:
                    logger.debug(f"namespace - {item['metadata']['name']}")
                    namespaces.append(f"{item['metadata']['name']}")
                result['success'] = True
                result['namespaces'] = namespaces
                logger.debug(f"{namespaces}")
        else:
            logger.error("Issue with authentication/authorisation")
            logger.error("Check token")
            logger.error(response.json())
            result['success'] = False
            result['namespaces'] = []
    except Exception:
        logger.error(traceback.format_exc())
        logger.error("Exception fetching namespace list")
    return result

def k8sgetServices(con_data, namespace):
    endpoint = con_data['api_server']
    #/api/v1/namespaces/{namespace}/services
    url = f"/v1/namespaces/{namespace}/services"
    try:
        response = requests.get(f"{endpoint}{url}", auth=BearerAuth(con_data['token']), verify=con_data['verify_ca'])
        # logger.debug(response.json())
        resp = response.json()
        result = {}
        if response.status_code == 200:
            # logger.debug("good response code")
            if "items" in resp:
                services = []
                # logger.debug("Got suitable response")
                for item in resp['items']:
                    logger.debug(f"service - {item['metadata']['name']}")
                    svc = {}
                    svc['name'] = item['metadata']['name']
                    svc['spec'] = item['spec']
                    svc['status'] = item['status']
                    services.append(svc)
                result['success'] = True
                result['services'] = services
                logger.debug(f"{services}")
        else:
            logger.error("Issue with authentication/authorisation")
            logger.error("Check token")
            logger.error(response.json())
            result['success'] = False
            result['services'] = []
    except Exception:
        logger.error(traceback.format_exc())
        logger.error("Exception fetching namespace list")
    return result

def k8sgetSecrets(con_data, namespace):
    endpoint = con_data['api_server']
    #/api/v1/namespaces/{namespace}/services
    url = f"/v1/namespaces/{namespace}/secrets"
    try:
        response = requests.get(f"{endpoint}{url}", auth=BearerAuth(con_data['token']), verify=con_data['verify_ca'])
        # logger.debug(response.json())
        resp = response.json()
        result = {}
        if response.status_code == 200:
            # logger.debug("good response code")
            if "items" in resp:
                services = []
                # logger.debug("Got suitable response")
                for item in resp['items']:
                    logger.debug(f"service - {item['metadata']['name']}")
                    svc = {}
                    svc['name'] = item['metadata']['name']
                    svc['spec'] = item['spec']
                    svc['status'] = item['status']
                    services.append(svc)
                result['success'] = True
                result['services'] = services
                logger.debug(f"{services}")
        else:
            logger.error("Issue with authentication/authorisation")
            logger.error("Check token")
            logger.error(response.json())
            result['success'] = False
            result['services'] = []
    except Exception:
        logger.error(traceback.format_exc())
        logger.error("Exception fetching namespace list")
    return result

def k8sgetIngresses(con_data, namespace):
    endpoint = con_data['api_server']
    #/api/v1/namespaces/{namespace}/ingresses
    url = f"/v1/namespaces/{namespace}/ingresses"
    try:
        response = requests.get(f"{endpoint}{url}", auth=BearerAuth(con_data['token']), verify=con_data['verify_ca'])
        # logger.debug(response.json())
        resp = response.json()
        result = {}
        if response.status_code == 200:
            # logger.debug("good response code")
            if "items" in resp:
                ings = []
                # logger.debug("Got suitable response")
                for item in resp['items']:
                    logger.debug(f"Ingress - {item['metadata']['name']}")
                    ing = {}
                    ing['name'] = item['metadata']['name']
                    ing['spec'] = item['spec']
                    ing['status'] = item['status']
                    ings.append(ing)
                result['success'] = True
                result['ingresses'] = ings
                logger.debug(f"{ings}")
        else:
            logger.error("Issue with authentication/authorisation")
            logger.error("Check token")
            logger.error(response.json())
            result['success'] = False
            result['ingresses'] = []
    except Exception:
        logger.error(traceback.format_exc())
        logger.error("Exception fetching ingresses list")
    return result
