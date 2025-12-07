import pytest
from httpx import AsyncClient


@pytest.fixture()
async def created_post(async_client: AsyncClient):
    """Example: created_post: {'body': 'Test Post', 'id': 3}"""
    body = "Test Post"
    response = await async_client.post("/post", json={"body": body})
    return response.json()


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient):
    body = "Test Post"
    response = await async_client.post("/post", json={"body": body})

    assert response.status_code == 201
    assert {"body": body}.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_missing_body(async_client: AsyncClient):
    response = await async_client.post("/post", json={})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/posts")

    assert response.status_code == 200
    # assert response.json() == [created_post]


### Test Comment ###
@pytest.fixture()
async def created_comment(async_client: AsyncClient, created_post: dict):
    body = "Test Comment"
    response = await async_client.post(
        "/comment", json={"body": body, "post_id": created_post.get("id")}
    )
    return response.json()


@pytest.mark.anyio
async def test_create_comment(async_client: AsyncClient, created_post: dict):
    # Create post
    print(f"created_post: {created_post}")

    # Create comment
    body = "Test Comment"
    response = await async_client.post(
        "/comment", json={"body": body, "post_id": created_post.get("id")}
    )
    assert response.status_code == 201
    assert {
        # "id": 1,
        "body": body,
        "post_id": created_post.get("id"),
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_on_post(async_client: AsyncClient, created_post: dict, created_comment: dict):
    response = await async_client.get(f"/posts/{created_post.get("id")}/comments")

    assert response.status_code == 200
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_comments_on_post_empty(async_client: AsyncClient, created_post: dict):
    response = await async_client.get(f"/posts/{created_post.get("id")}/comments")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_post_with_comments(async_client: AsyncClient, created_post: dict, created_comment: dict):
    response = await async_client.get(f"/posts/{created_post.get("id")}")

    assert response.status_code == 200
    assert response.json() == {"post": created_post, "comments": [created_comment]}


@pytest.mark.anyio
async def test_get_missing_post_with_comments(async_client: AsyncClient, created_post: dict, created_comment: dict):
    response = await async_client.get("/posts/120")
    assert response.status_code == 404
