import os
from dotenv import load_dotenv

load_dotenv(override=True)

def is_local():
    ENV = os.getenv("ENVIRONMENT", "CLOUD")
    return ENV.upper() == "LOCAL"

def get_env_var(key, default=None):
    try: 
        env_val = os.getenv(key, default)
    except KeyError:
        print(f"[WARNING] {key} environment variable not set. Using default")        
        env_val = default   
    return env_val
