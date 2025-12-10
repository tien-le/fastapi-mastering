"""Tests for post and comment endpoints."""
import pytest
from httpx import AsyncClient
from fastapi import status


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


@pytest.fixture()
async def created_like_post(async_client: AsyncClient, created_post: dict, logged_in_token: str) -> dict:
    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.anyio
async def test_like_post(async_client: AsyncClient, created_post: dict, logged_in_token: str):
    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    like_posts = response.json()
    assert isinstance(like_posts, dict)
    assert len(like_posts) >= 1


# Post Tests
@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient, confirmed_user: dict, logged_in_token: str):
    """Test creating a new post."""
    body = "Test Post"
    response = await async_client.post("/post", json={"body": body}, headers={"Authorization": f"Bearer {logged_in_token}"})

    assert response.status_code == 201
    data = response.json()
    assert data["body"] == body
    assert "id" in data
    assert isinstance(data["id"], int)
    assert data["user_id"] == confirmed_user["id"]


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
@pytest.mark.parametrize(
    "sorting, expected_order",
    [
        ("new", [2, 1]),
        ("old", [1, 2]),
        ("most_likes", [1, 2])
    ]
)
async def test_get_all_posts_sorting(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_order: list[int],
):
    """Test getting all posts with different sorting options."""
    headers = {"Authorization": f"Bearer {logged_in_token}"}

    # Create two new posts
    response1 = await async_client.post(
        "/post",
        json={"body": "Test Post 1"},
        headers=headers
    )
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = await async_client.post(
        "/post",
        json={"body": "Test Post 2"},
        headers=headers
    )
    assert response2.status_code == status.HTTP_201_CREATED

    response3 = await async_client.post(
        "/like",
        json={"post_id": 1},
        headers=headers
    )
    assert response3.status_code == status.HTTP_201_CREATED

    # Get all posts with specified sorting
    response = await async_client.get(
        "/posts",
        params={"sorting": sorting},
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK

    # Filter out the fixture post and extract IDs
    posts = response.json()
    post_ids = [post["id"] for post in posts]

    # Verify the order matches expected sorting
    assert post_ids == expected_order


@pytest.mark.anyio
async def test_get_all_posts_sorting_new(async_client: AsyncClient, logged_in_token: str):
    """Test getting all posts sorted by newest first."""
    headers = {"Authorization": f"Bearer {logged_in_token}"}

    # Create two new posts
    response1 = await async_client.post(
        "/post",
        json={"body": "Test Post 1"},
        headers=headers
    )
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = await async_client.post(
        "/post",
        json={"body": "Test Post 2"},
        headers=headers
    )
    assert response2.status_code == status.HTTP_201_CREATED

    # Get all posts sorted by newest first
    response = await async_client.get(
        "/posts",
        params={"sorting": "new"},
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK

    # Filter out the fixture post and extract IDs
    posts = response.json()
    post_ids = [post["id"] for post in posts]

    # Verify posts are sorted newest first (descending ID order)
    assert post_ids == [2, 1]


@pytest.mark.anyio
async def test_get_all_posts_sorting_old(async_client: AsyncClient, logged_in_token: str):
    """Test getting all posts sorted by oldest first."""
    headers = {"Authorization": f"Bearer {logged_in_token}"}

    # Create two new posts
    response1 = await async_client.post(
        "/post",
        json={"body": "Test Post 1"},
        headers=headers
    )
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = await async_client.post(
        "/post",
        json={"body": "Test Post 2"},
        headers=headers
    )
    assert response2.status_code == status.HTTP_201_CREATED

    # Get all posts sorted by oldest first
    response = await async_client.get(
        "/posts",
        params={"sorting": "old"},
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK

    # Filter out the fixture post and extract IDs
    posts = response.json()
    post_ids = [post["id"] for post in posts]

    # Verify posts are sorted oldest first (ascending ID order)
    assert post_ids == [1, 2]


@pytest.mark.anyio
async def test_get_all_posts_sorting_most_likes(async_client: AsyncClient, logged_in_token: str):
    """Test getting all posts sorted by most likes."""
    headers = {"Authorization": f"Bearer {logged_in_token}"}

    # Create two new posts
    response1 = await async_client.post(
        "/post",
        json={"body": "Test Post 1"},
        headers=headers
    )
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = await async_client.post(
        "/post",
        json={"body": "Test Post 2"},
        headers=headers
    )
    assert response2.status_code == status.HTTP_201_CREATED

    response3 = await async_client.post(
        "/like",
        json={"post_id": 1},
        headers=headers
    )
    assert response3.status_code == status.HTTP_201_CREATED

    response = await async_client.get(
        "/posts",
        params={"sorting": "most_likes"},
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK

    # Filter out the fixture post and extract IDs
    posts = response.json()
    post_ids = [post["id"] for post in posts]

    # Verify posts are sorted oldest first (ascending ID order)
    assert post_ids == [1, 2]


@pytest.mark.anyio
async def test_get_all_posts_sorting_wrong(async_client: AsyncClient, logged_in_token: str):
    headers = {"Authrization": f"Bearer {logged_in_token}"}

    response = await async_client.get(
        "/posts",
        params={"sorting": "wrong_info"},
        headers=headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


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
async def test_create_comment(async_client: AsyncClient, created_post: dict, confirmed_user:dict, logged_in_token: str):
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
    assert data["user_id"] == confirmed_user["id"]


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
    assert response.status_code == status.HTTP_200_OK
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


