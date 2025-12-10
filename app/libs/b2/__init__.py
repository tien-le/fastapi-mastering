
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
    except Exception:
        bucket = b2_api.create_bucket(bucket_name, 'allPrivate')
    return bucket


def upload_file(local_file: str, file_name: str) -> str:
    b2_api = get_b2_api()
    logger.debug(f"Uploading {local_file} to Bucket as {file_name}")
    uploaded_file = get_bucket().upload_local_file(
        local_file=local_file, file_name=file_name
    )
    download_url = b2_api.get_download_url_for_fileid(uploaded_file.id_)
    return download_url


def build_file_path(tenant_id: str, language: str | None, user_id: str, file_name: str) -> str:
    """Build file path following the structure: tenant_id/language/users/user_id/file_name"""
    path_parts = [tenant_id]
    if language:
        path_parts.append(language)
    path_parts.extend(["users", user_id, file_name])
    return "/".join(path_parts)


def upload_file_to_language_bucket(
    bucket: Bucket,
    tenant_id: str,
    language: str | None,
    user_id: str,
    file_name: str,
    data: bytes
):
    """Upload file to bucket with proper path structure: tenant_id/language/users/user_id/file_name"""
    file_path = build_file_path(tenant_id, language, user_id, file_name)
    logger.debug(f"Uploading file to path: {file_path}")
    return bucket.upload_bytes(data, file_path)


def upload_file_with_path(
    tenant_id: str,
    language: str | None,
    user_id: str,
    local_file: str,
    file_name: str
) -> str:
    """Upload local file to bucket with proper path structure and return download URL"""
    b2_api = get_b2_api()
    bucket = get_bucket()
    file_path = build_file_path(tenant_id, language, user_id, file_name)
    logger.debug(f"Uploading {local_file} to Bucket as {file_path}")
    uploaded_file = bucket.upload_local_file(
        local_file=local_file, file_name=file_path
    )
    download_url = b2_api.get_download_url_for_fileid(uploaded_file.id_)
    return download_url



