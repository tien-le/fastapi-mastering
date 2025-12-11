"""Post and comment router module using FastAPI, SQLAlchemy 2.0, and Pydantic 2.0."""
from enum import Enum
import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc

from app.core.database import get_async_session
from app.entities.schemas import (
    UserPost,
    UserPostIn,
    Comment,
    CommentIn,
    UserPostWithComments,
    UserPostWithLikes,
    User,
    UserIn,
    PostLikeIn,
    PostLike
)
from app.entities.models import Post, Comment as CommentORM, User as UserORM, Like
from app.routers.user import oauth2_scheme, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["posts"])


select_post_and_likes = (
    select(Post, func.count(Like.id).label("likes"))
    .outerjoin(Like, Like.post_id == Post.id)
    .group_by(Post.id)
)


# Dependencies
async def get_post_by_id(
    post_id: Annotated[int, Path(gt=0, description="The ID of the post")],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Post:
    """
    Dependency to fetch a post by ID.

    Raises:
        HTTPException: 404 if post not found
    """
    query = select(Post).where(Post.id == post_id)
    logger.debug(f"Fetching post with id={post_id}")
    result = await session.execute(query)
    post: Post | None = result.scalar_one_or_none()

    if post is None:
        logger.warning(f"Post with id={post_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id={post_id} not found",
        )

    return post


# Utility functions
async def _find_post(session: AsyncSession, post_id: int) -> Post | None:
    """Internal utility to find a post without raising exceptions."""
    # query = select(Post).where(Post.id == post_id)
    query = select_post_and_likes.where(Post.id == post_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


def _convert_post_to_entity(post: Post) -> UserPost:
    """Convert ORM Post to Pydantic UserPost entity."""
    return UserPost.model_validate(post, from_attributes=True)


def _convert_post_with_likes_to_entity(post: Post, likes: int) -> UserPostWithLikes:
    """Convert ORM Post with likes count to Pydantic UserPostWithLikes entity."""
    post_dict = {
        "id": post.id,
        "body": post.body,
        "user_id": post.user_id,
        "likes": likes
    }
    return UserPostWithLikes.model_validate(post_dict)


def _convert_comment_to_entity(comment: CommentORM) -> Comment:
    """Convert ORM Comment to Pydantic Comment entity."""
    return Comment.model_validate(comment, from_attributes=True)


def _convert_post_like_to_entity(post_like: Like) -> PostLike:
    """Convert ORM Like to Pydantic PostLike entity."""
    return PostLike.model_validate(post_like, from_attributes=True)


# Post endpoints
@router.post(
    "/post",
    response_model=UserPost,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new post",
    description="Creates a new post with the provided body content",
)
async def create_post(
    post: UserPostIn,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[UserIn, Depends(get_current_user)]
    # request: Request
) -> UserPost:
    """Create a new post."""
    logger.info(f"Creating new post with body length: {len(post.body)}")

    # token = await oauth2_scheme(request)
    # current_user = await get_current_user(session=session, token=token)
    logger.info(f"Got current user: {current_user}")

    new_post = Post(**post.model_dump(), user_id=current_user.id)
    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)
    logger.debug(f"Created post with id={new_post.id}")
    return _convert_post_to_entity(new_post)


class PostSorting(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"


@router.get(
    "/posts",
    response_model=list[UserPost],
    summary="Get all posts",
    description="Retrieves all posts from the database",
)
async def get_posts(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    sorting: PostSorting = PostSorting.new
) -> list[UserPost]:
    """Get all posts."""
    logger.info("Fetching all posts")
    # query = select(Post)
    if sorting == PostSorting.new:
        query = select_post_and_likes.order_by(desc(Post.id))
    elif sorting == PostSorting.old:
        query = select_post_and_likes.order_by(asc(Post.id))
    elif sorting == PostSorting.most_likes:
        query = select_post_and_likes.order_by(desc("likes"))
    else:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Missing information of sorting"
        )

    result = await session.execute(query)
    posts = result.scalars().all()
    logger.debug(f"Found {len(posts)} posts")
    return [_convert_post_to_entity(post) for post in posts]


# Comment endpoints
@router.get(
    "/comments",
    response_model=list[Comment],
    summary="Get all comments",
    description="Retrieves all comments from the database",
)
async def get_comments(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[Comment]:
    """Get all comments."""
    logger.info("Fetching all comments")
    result = await session.execute(select(CommentORM))
    comments = result.scalars().all()
    logger.debug(f"Found {len(comments)} comments")
    return [_convert_comment_to_entity(comment) for comment in comments]


@router.post(
    "/comment",
    response_model=Comment,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new comment",
    description="Creates a new comment for a specific post",
)
async def create_comment(
    comment: CommentIn,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[UserIn, Depends(get_current_user)]
    # request: Request
) -> Comment:
    """Create a new comment for a post."""
    logger.info(f"Creating comment for post_id={comment.post_id}")

    # token = await oauth2_scheme(request)
    # current_user = await get_current_user(session=session, token=token)
    logger.info(f"Got current user: {current_user}")

    # Validate post exists
    post = await _find_post(session, comment.post_id)
    if post is None:
        logger.warning(f"Post with id={comment.post_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id={comment.post_id} not found",
        )

    new_comment = CommentORM(**comment.model_dump(), user_id=current_user.id)
    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)
    logger.debug(f"Created comment with id={new_comment.id}")
    return _convert_comment_to_entity(new_comment)


@router.get(
    "/posts/{post_id}/comments",
    response_model=list[Comment],
    summary="Get comments for a post",
    description="Retrieves all comments associated with a specific post",
)
async def get_comments_on_post(
    post: Annotated[Post, Depends(get_post_by_id)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[Comment]:
    """Get all comments for a specific post."""
    logger.info(f"Fetching comments for post_id={post.id}")
    query = select(CommentORM).where(CommentORM.post_id == post.id)
    result = await session.execute(query)
    comments = result.scalars().all()
    logger.debug(f"Found {len(comments)} comments for post_id={post.id}")
    return [_convert_comment_to_entity(comment) for comment in comments]


@router.get(
    "/posts/{post_id}",
    response_model=UserPostWithComments,
    summary="Get post with comments",
    description="Retrieves a specific post along with all its comments",
)
async def get_post_with_comments(
    post_id: Annotated[int, Path(gt=0, description="The ID of the post")],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> UserPostWithComments:
    """Get a post with all its comments.

    Efficiently loads comments using SQLAlchemy 2.0 select query.
    """
    logger.info(f"Fetching post with comments for post_id={post_id}")

    # Query post with likes count
    query = select_post_and_likes.where(Post.id == post_id)
    result = await session.execute(query)
    row = result.first()

    if row is None:
        logger.warning(f"Post with id={post_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id={post_id} not found",
        )

    # Unpack the Row object: (Post, likes_count)
    post = row[0]
    likes_count = row[1]
    likes = likes_count or 0

    # Query comments for this post using SQLAlchemy 2.0 style
    comment_query = select(CommentORM).where(CommentORM.post_id == post_id).order_by(CommentORM.id)
    comment_result = await session.execute(comment_query)
    comment_rows = comment_result.scalars().all()
    comments = [_convert_comment_to_entity(comment) for comment in comment_rows]
    logger.debug(f"Found {len(comments)} comments for post_id={post_id}")
    return UserPostWithComments(
        post=_convert_post_with_likes_to_entity(post, likes), comments=comments
    )


@router.post(
    "/like",
    response_model=PostLike,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new post like",
    description="Creates a like for a post"
)
async def like_post(
    post_like: PostLikeIn,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[UserIn, Depends(get_current_user)]
) -> PostLike:
    """Creates a like for a post"""
    logger.info(f"Creating a like for post_id: {post_like.post_id}")

    logger.info(f"Got current user: {current_user}")

    # Validate post exists
    post = await _find_post(session, post_like.post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post Not Found with post_id={post_like.post_id}"
        )

    new_post_like = Like(**post_like.model_dump(), user_id=current_user.id)
    session.add(new_post_like)
    await session.commit()
    await session.refresh(new_post_like)
    logger.debug(f"Created post like with id={new_post_like.id}")
    return _convert_post_like_to_entity(new_post_like)
