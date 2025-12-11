"""Pydantic models for request/response validation using Pydantic 2.0."""
from pydantic import BaseModel, ConfigDict, Field


class UserPostIn(BaseModel):
    """Input model for creating a new post.

    Attributes:
        body: The content of the post (can be empty)
    """

    body: str = Field(..., description="The content of the post")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "body": "This is a sample post content",
            }
        }
    )


class UserPost(UserPostIn):
    """Output model for a post.

    Attributes:
        id: Unique identifier for the post
        body: The content of the post
        user_id: Unique identifier for user
        image_url: Image URL (optional)
    """

    id: int = Field(..., gt=0, description="Unique identifier for the post")
    user_id: int = Field(..., gt=0, description="Unique identifier for user")
    image_url: str | None = Field(default=None, description="Image URL")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "body": "This is a sample post content",
                "user_id": 1,
                "image_url": None
            }
        },
    )


class CommentIn(BaseModel):
    """Input model for creating a new comment.

    Attributes:
        body: The content of the comment (can be empty)
        post_id: The ID of the post this comment belongs to
    """

    body: str = Field(..., description="The content of the comment")
    post_id: int = Field(..., gt=0, description="The ID of the post this comment belongs to")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "body": "This is a sample comment",
                "post_id": 1,
            }
        }
    )


class Comment(CommentIn):
    """Output model for a comment.

    Attributes:
        id: Unique identifier for the comment
        body: The content of the comment
        post_id: The ID of the post this comment belongs to
    """

    id: int = Field(..., gt=0, description="Unique identifier for the comment")
    user_id: int = Field(..., gt=0, description="Unique identifier for user")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "body": "This is a sample comment",
                "post_id": 1,
                "user_id": 1,
            }
        },
    )


class UserPostWithLikes(UserPost):
    """Output model for a post with likes count.

    Attributes:
        id: Unique identifier for the post
        body: The content of the post
        user_id: Unique identifier for user
        image_url: Image URL (optional)
        likes: Number of likes on the post
    """
    likes: int = Field(..., ge=0, description="Number of likes")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "body": "This is a sample post content",
                "user_id": 1,
                "likes": 2
            }
        },
    )


class UserPostWithComments(BaseModel):
    """Output model for a post with all its comments.

    Attributes:
        post: The post data
        comments: List of comments associated with the post
    """

    post: UserPostWithLikes = Field(..., description="The post data with likes")
    comments: list[Comment] = Field(default_factory=list, description="List of comments")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "post": {
                    "id": 1,
                    "body": "This is a sample post",
                    "user_id": 1,
                    "likes": 2
                },
                "comments": [
                    {
                        "id": 1,
                        "body": "This is a comment",
                        "post_id": 1,
                    }
                ],
            }
        }
    )


class User(BaseModel):
    """Output model for a user.

    Attributes:
        id: Unique identifier for user
        email: Email of user
    """
    id: int = Field(..., gt=0, description="Unique identifier for user")
    email: str = Field(..., description="Email of user")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "test_email@gmail.com",
            }
        }
    )


class UserIn(User):
    """Input model for creating a new user.

    Attributes:
        password: Password of user
    """
    password: str = Field(..., description="Password of user")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "test_email@gmail.com",
                "password": "test_password",
            }
        }
    )


class UserRegistrationResponse(BaseModel):
    """Response model for user registration.

    Attributes:
        id: Unique identifier for user
        email: Email of user
        detail: Registration message
        confirmation_url: URL for email confirmation
    """
    id: int = Field(..., gt=0, description="Unique identifier for user")
    email: str = Field(..., description="Email of user")
    detail: str = Field(..., description="Registration message")
    confirmation_url: str = Field(..., description="URL for email confirmation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "test_email@gmail.com",
                "detail": "User created. Please confirm your email.",
                "confirmation_url": "http://testserver/confirm/token123",
            }
        }
    )



class PostLikeIn(BaseModel):
    """Input model for creating a new post like.

    Attributes:
        post_id: The ID of the post to like
    """
    post_id: int = Field(..., gt=0, description="The ID of the post to like")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "post_id": 1,
            }
        }
    )


class PostLike(PostLikeIn):
    """Output model for a post like.

    Attributes:
        id: Unique identifier for the post like
        user_id: Unique identifier for user
        post_id: The ID of the post that was liked
    """
    id: int = Field(..., gt=0, description="Unique identifier for the post like")
    user_id: int = Field(..., gt=0, description="Unique identifier for user")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "post_id": 1,
            }
        }
    )
