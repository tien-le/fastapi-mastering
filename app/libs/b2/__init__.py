
import logging
from functools import lru_cache

from b2sdk.v2 import InMemoryAccountInfo, B2Api
from b2sdk.v2 import Bucket

from app.core.config_loader import settings


logger = logging.getLogger(__name__)

"""
tenant_id/
   language/
       users/
           user_id/
               file1.txt
               file2.txt

This approach supports:
    Multi-tenants → separate buckets or prefixed folders
    Multi-languages → language subfolders
    Multi-users → user subfolders
    FastAPI handles uploads, listing, and access control
    Backblaze B2 handles storage and scaling
    Upload big file
"""


@lru_cache()
def get_b2_api() -> B2Api:
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)

    B2_KEY_ID = settings.B2_KEY_ID
    B2_APPLICATION_KEY = settings.B2_APPLICATION_KEY

    b2_api.authorize_account("production", B2_KEY_ID, B2_APPLICATION_KEY)
    return b2_api


@lru_cache()
def get_bucket(bucket_name: str | None = None) -> Bucket:
    try:
        bucket_name = bucket_name or settings.B2_BUCKET_NAME
        logger.info(f"Get bucket name: {bucket_name}")
        b2_api = get_b2_api()
        bucket = b2_api.get_bucket_by_name(bucket_name)
    except Exception: # Bucket doesn't exist
        logger.info(f"Bucket {bucket_name} not found. Creating...")
        bucket = b2_api.create_bucket(bucket_name, 'allPrivate')
    return bucket


def upload_file(local_file: str, file_name: str, overwrite: bool=True) -> str:
    b2_api = get_b2_api()
    bucket = get_bucket()  # Ensure we have the bucket object
    logger.debug(f"Uploading {local_file} to bucket as {file_name}")

    uploaded_file = bucket.upload_local_file(
        local_file=local_file, file_name=file_name
    )
    download_url = b2_api.get_download_url_for_fileid(uploaded_file.id_)
    logger.debug(f"Uploaded {local_file} successfully. Download URL: {download_url}")

    ## Delete old versions (true overwrite)
    if overwrite:
        for file_version in bucket.ls(file_name=file_name, show_versions=True):
            if file_version.id_ != uploaded_file.id_:  # skip the newly uploaded one
                logger.debug(f"Deleting old version {file_version.id_} of {file_name}")
                bucket.delete_file_version(file_version.id_, file_version.file_name)
    return download_url

