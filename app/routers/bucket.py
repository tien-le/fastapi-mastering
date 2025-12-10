from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
import logging
import os
import tempfile
import aiofiles

from app.libs.b2 import get_bucket, upload_file_with_path

logger = logging.getLogger(__name__)
router = APIRouter()

# client -> server (tempfile) -> Bucket -> delete tempfile

# client split up file into chunks about 1MB
# client sends up chunks 1 at a time
# client sends the last chunk
CHUNK_SIZE = 1024 * 1024  # 1MB

@router.post("/upload/", status_code=status.HTTP_201_CREATED)
async def upload_file(
    tenant_id: str = Form("1"),
    user_id: str = Form("1"),
    language: str = Form("en"),
    file: UploadFile = File(...)  # ... (Ellipsis) -> this is required.
):
    """Upload file with multi-tenant, multi-language, multi-user support.

    File structure: tenant_id/language/users/user_id/filename
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            filename = tf.name
            logger.info(f"Saving uploaded file temporarily to {filename}")
            async with aiofiles.open(filename, "wb") as f:
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)

            file_url = upload_file_with_path(
                tenant_id=tenant_id,
                language=language,
                user_id=user_id,
                local_file=filename,
                file_name=file.filename
            )

            # Clean up temp file
            os.unlink(filename)

        return {
            "detail": f"Successfully uploaded {file.filename}",
            "file_url": file_url,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "language": language
        }
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error when uploading file: {str(e)}"
        )


@router.get("/files/")
def list_files(
    tenant_id: str = "1",
    user_id: str = "1",
    language: str = "en"
):
    """List files for a tenant, optionally filtered by language and user_id.

    Returns files matching the path structure: tenant_id/language/users/user_id/*
    """
    try:
        bucket = get_bucket()

        # Build prefix to filter files
        prefix_parts = [tenant_id]
        if language:
            prefix_parts.append(language)
        prefix_parts.append("users")
        if user_id:
            prefix_parts.append(user_id)

        prefix = "/".join(prefix_parts) + "/"

        logger.info(f"Listing files with prefix: {prefix}")

        # List files with the prefix
        files = []
        for file_info in bucket.ls(folder_to_list=prefix):
            files.append({
                "file_name": file_info.file_name,
                "file_id": file_info.id_,
                "size": file_info.size,
                "upload_timestamp": file_info.upload_timestamp
            })

        return {
            "tenant_id": tenant_id,
            "language": language,
            "user_id": user_id,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error when listing files: {str(e)}"
        )


