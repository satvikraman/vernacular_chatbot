import os
from google.api_core import exceptions
from google.cloud import storage
from app.utils.env import is_local, get_env_var

GCS_AUDIO_LOG_BUCKET = get_env_var("GCS_AUDIO_LOG_BUCKET", "error-bucket-name")
storage_client = storage.Client()

def upload_to_gcs(local_file_path, user_id):
    # Use user_id and a unique filename to prevent collisions and aid debugging
    original_filename = os.path.basename(local_file_path)
    uploaded_blob_name = f"input_audio/{user_id}/{original_filename}"
    full_gcs_uri = f"gs://{GCS_AUDIO_LOG_BUCKET}/{uploaded_blob_name}"

    if is_local():
        return full_gcs_uri

    try:
        bucket = storage_client.bucket(GCS_AUDIO_LOG_BUCKET)
        blob = bucket.blob(uploaded_blob_name)
        blob.upload_from_filename(local_file_path)
        print(f"[INFO] Successfully uploaded {local_file_path} to {full_gcs_uri}")
        return full_gcs_uri
    except exceptions.NotFound:
        # Handles cases where the bucket does not exist or the client cannot find it
        print(f"[ERROR] GCS Bucket not found: {GCS_AUDIO_LOG_BUCKET}")
        # Consider re-raising or returning a specific error/empty string
        raise
    except exceptions.GoogleAPICallError as e:
        # Handles network issues, permission errors, etc.
        print(f"[ERROR] GCS Upload failed for {local_file_path}: {e}")
        # Consider re-raising or returning a specific error/empty string
        raise
    except FileNotFoundError:
        # Handles case where the local file doesn't exist
        print(f"[ERROR] Local file not found: {local_file_path}")
        raise

