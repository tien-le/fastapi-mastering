from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
import logging
import os
import tempfile
import aiofiles

from app.libs.b2 import get_bucket, upload_file as upload_file_to_bucket

logger = logging.getLogger(__name__)
router = APIRouter()

# client -> server (tempfile) -> Bucket -> delete tempfile

# client split up file into chunks about 1MB
# client sends up chunks 1 at a time
# client sends the last chunk
CHUNK_SIZE = 1024 * 1024  # 1MB

@router.post("/upload/", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...)  # ... (Ellipsis) -> this is required.
):
    """Upload file to bucker"""
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            filename = tf.name
            logger.info(f"Saving uploaded file temporarily to {filename}")
            async with aiofiles.open(filename, "wb") as f:
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)

            file_url = upload_file_to_bucket(local_file=filename, file_name=file.filename)

            # Clean up temp file
            os.unlink(filename)

        return {
            "detail": f"Successfully uploaded {file.filename}",
            "file_url": file_url
        }
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error when uploading file: {str(e)}"
        )


@router.get("/files/")
def list_files():
    """List files"""
    try:
        bucket = get_bucket()

        logger.info("Listing all files")

        # List all files
        files = []
        for file_info in bucket.ls():
            files.append({
                "file_name": file_info.file_name,
                "file_id": file_info.id_,
                "size": file_info.size,
                "upload_timestamp": file_info.upload_timestamp
            })

        return {
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error when listing files: {str(e)}"
        )


