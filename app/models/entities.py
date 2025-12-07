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


class UserPost(BaseModel):
    """Output model for a post.

    Attributes:
        id: Unique identifier for the post
        body: The content of the post
    """

    id: int = Field(..., gt=0, description="Unique identifier for the post")
    body: str = Field(..., description="The content of the post")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "body": "This is a sample post content",
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


class Comment(BaseModel):
    """Output model for a comment.

    Attributes:
        id: Unique identifier for the comment
        body: The content of the comment
        post_id: The ID of the post this comment belongs to
    """

    id: int = Field(..., gt=0, description="Unique identifier for the comment")
    body: str = Field(..., description="The content of the comment")
    post_id: int = Field(..., gt=0, description="The ID of the post this comment belongs to")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "body": "This is a sample comment",
                "post_id": 1,
            }
        },
    )


class UserPostWithComments(BaseModel):
    """Output model for a post with all its comments.

    Attributes:
        post: The post data
        comments: List of comments associated with the post
    """

    post: UserPost = Field(..., description="The post data")
    comments: list[Comment] = Field(default_factory=list, description="List of comments")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "post": {
                    "id": 1,
                    "body": "This is a sample post",
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
