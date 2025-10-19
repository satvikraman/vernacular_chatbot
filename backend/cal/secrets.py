# cal/secrets.py
import os
import json
from app.utils.env import is_local, get_env_var
from app.utils.config import get_config
from google.cloud import secretmanager_v1

SECRETS_CACHE = {}

# Load all secrets locally if local
if is_local():
    local_secrets_path = get_config("LOCAL_SECRETS_PATH", "secrets.local.json")
    with open(local_secrets_path) as f:
        SECRETS_CACHE = json.load(f)

def get_secret(key: str) -> str:
    """Get a secret by key — from local file or GCP Secret Manager"""
    project_id = get_config("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError("GCP_PROJECT_ID is not set in config")
    if is_local():
        return SECRETS_CACHE.get(key)

    if key in SECRETS_CACHE:
        return SECRETS_CACHE[key]

    # Get GCP project ID from config, not environment
    project_id = get_config("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError("GCP_PROJECT_ID is not set in config")

    client = secretmanager_v1.SecretManagerServiceClient()
    secret_name = f"projects/{project_id}/secrets/{key}/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    secret_value = response.payload.data.decode("UTF-8")
    SECRETS_CACHE[key] = secret_value
    return secret_value
