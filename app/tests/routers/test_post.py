"""Tests for post and comment endpoints."""
import pytest
from httpx import AsyncClient


# Fixtures
@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str) -> dict:
    """Create a test post and return its data."""
    body = "Test Post"
    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture()
async def created_comment(async_client: AsyncClient, created_post: dict, logged_in_token: str) -> dict:
    """Create a test comment and return its data."""
    body = "Test Comment"
    response = await async_client.post(
        "/comment", json={"body": body, "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 201
    return response.json()


# Post Tests
@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient, registered_user: dict, logged_in_token: str):
    """Test creating a new post."""
    body = "Test Post"
    response = await async_client.post("/post", json={"body": body}, headers={"Authorization": f"Bearer {logged_in_token}"})

    assert response.status_code == 201
    data = response.json()
    assert data["body"] == body
    assert "id" in data
    assert isinstance(data["id"], int)
    assert data["user_id"] == registered_user["id"]


@pytest.mark.anyio
async def test_create_post_missing_body(async_client: AsyncClient, logged_in_token: str):
    """Test creating a post without body field."""
    response = await async_client.post("/post", json={}, headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_post_empty_body(async_client: AsyncClient, logged_in_token: str):
    """Test creating a post with empty body."""
    response = await async_client.post("/post", json={"body": ""}, headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["body"] == ""


@pytest.mark.anyio
async def test_get_all_posts_empty(async_client: AsyncClient, logged_in_token: str):
    """Test getting all posts when none exist."""
    response = await async_client.get("/posts", headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict, logged_in_token: str):
    """Test getting all posts."""
    response = await async_client.get("/posts", headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 200
    posts = response.json()
    assert isinstance(posts, list)
    assert len(posts) >= 1
    assert any(post["id"] == created_post["id"] for post in posts)


@pytest.mark.anyio
async def test_get_post_with_comments_not_found(async_client: AsyncClient, logged_in_token: str):
    """Test getting a non-existent post with comments."""
    response = await async_client.get("/posts/99999", headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_get_post_with_comments_empty(async_client: AsyncClient, created_post: dict, logged_in_token: str):
    """Test getting a post with no comments."""
    response = await async_client.get(f"/posts/{created_post['id']}", headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["post"]["id"] == created_post["id"]
    assert data["post"]["body"] == created_post["body"]
    assert data["comments"] == []


# Comment Tests
@pytest.mark.anyio
async def test_create_comment(async_client: AsyncClient, created_post: dict, registered_user:dict, logged_in_token: str):
    """Test creating a new comment."""
    body = "Test Comment"
    response = await async_client.post(
        "/comment", json={"body": body, "post_id": created_post["id"]}
        , headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["body"] == body
    assert data["post_id"] == created_post["id"]
    assert "id" in data
    assert isinstance(data["id"], int)
    assert data["user_id"] == registered_user["id"]


@pytest.mark.anyio
async def test_create_comment_missing_post_id(async_client: AsyncClient, logged_in_token: str):
    """Test creating a comment without post_id."""
    response = await async_client.post("/comment", json={"body": "Test"}, headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_comment_missing_body(async_client: AsyncClient, created_post: dict, logged_in_token: str):
    """Test creating a comment without body."""
    response = await async_client.post(
        "/comment", json={"post_id": created_post["id"]}, headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_comment_invalid_post_id(async_client: AsyncClient, logged_in_token: str):
    """Test creating a comment with non-existent post_id."""
    response = await async_client.post(
        "/comment", json={"body": "Test", "post_id": 99999}, headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_get_all_comments_empty(async_client: AsyncClient, logged_in_token: str):
    """Test getting all comments when none exist."""
    response = await async_client.get("/comments", headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_all_comments(async_client: AsyncClient, created_comment: dict, logged_in_token: str):
    """Test getting all comments."""
    response = await async_client.get("/comments", headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 200
    comments = response.json()
    assert isinstance(comments, list)
    assert len(comments) >= 1
    assert any(comment["id"] == created_comment["id"] for comment in comments)


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict, logged_in_token: str
):
    """Test getting comments for a specific post."""
    response = await async_client.get(f"/posts/{created_post['id']}/comments", headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 200
    comments = response.json()
    assert isinstance(comments, list)
    assert len(comments) >= 1
    assert any(comment["id"] == created_comment["id"] for comment in comments)


@pytest.mark.anyio
async def test_get_comments_on_post_empty(async_client: AsyncClient, created_post: dict, logged_in_token: str):
    """Test getting comments for a post with no comments."""
    response = await async_client.get(f"/posts/{created_post['id']}/comments", headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_comments_on_post_not_found(async_client: AsyncClient, logged_in_token: str):
    """Test getting comments for a non-existent post."""
    response = await async_client.get("/posts/99999/comments", headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict, logged_in_token: str
):
    """Test getting a post with its comments."""
    response = await async_client.get(f"/posts/{created_post['id']}", headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["post"]["id"] == created_post["id"]
    assert data["post"]["body"] == created_post["body"]
    assert isinstance(data["comments"], list)
    assert len(data["comments"]) >= 1
    assert any(
        comment["id"] == created_comment["id"] for comment in data["comments"]
    )


@pytest.mark.anyio
async def test_get_post_with_comments_invalid_id(async_client: AsyncClient, logged_in_token: str):
    """Test getting a post with invalid ID."""
    response = await async_client.get("/posts/0", headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 422  # Validation error for Path(gt=0)


@pytest.mark.anyio
async def test_get_post_with_comments_negative_id(async_client: AsyncClient, logged_in_token: str):
    """Test getting a post with negative ID."""
    response = await async_client.get("/posts/-1", headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 422  # Validation error for Path(gt=0)
