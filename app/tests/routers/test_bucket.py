import contextlib
import os
import pathlib
import tempfile

import pytest
from httpx import AsyncClient

@pytest.fixture()
def sample_image(fs) -> pathlib.Path:
	path = (pathlib.Path(__file__).parent/"asserts"/"myfile.png").resolve()
	fs.create_file(path)
	return path


@pytest.fixture(autouse=True)
def mock_b2_upload_file(mocker):
	return mocker.patch("app.routers.bucket.upload_file", return_value="https://fakeurl.com")


