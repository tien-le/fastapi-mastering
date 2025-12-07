from app.models.entities import (
    UserPost,
    UserPostIn,
    Comment,
    CommentIn,
    UserPostWithComments,
)
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.orm import Post, Comment as CommentORM  # models.orm
from app.core.database import get_async_session

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Utility
async def find_post(session: AsyncSession, post_id: int) -> UserPost | None:
    query = select(Post).where(Post.id == post_id)
    logger.debug(f"find_post with query={query}")
    result = await session.execute(query)
    post: Post | None = result.scalar_one_or_none()
    if post is None:
        return None
    # Convert ORM -> pydantic
    return UserPost.model_validate(post, from_attributes=True)


### Post ###
@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostIn, session: AsyncSession = Depends(get_async_session)
):
    new_post = Post(**post.model_dump())
    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)
    return UserPost.model_validate(new_post, from_attributes=True)


@router.get("/posts", response_model=list[UserPost])
async def get_posts(session: AsyncSession = Depends(get_async_session)):
    logger.info("Getting all posts")
    result = await session.execute(select(Post))
    posts = result.scalars().all()
    return [UserPost.model_validate(p, from_attributes=True) for p in posts]


### Comment ###


@router.get("/comments", response_model=list[Comment])
async def get_comments(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(CommentORM))
    comments = result.scalars().all()
    return [Comment.model_validate(c, from_attributes=True) for c in comments]


@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(
    comment: CommentIn, session: AsyncSession = Depends(get_async_session)
):
    post = await find_post(session, comment.post_id)
    if post is None:
        raise HTTPException(
            status_code=404, detail=f"Post Not Found based on post_id={comment.post_id}"
        )

    new_comment = CommentORM(**comment.model_dump())
    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)

    return Comment.model_validate(new_comment, from_attributes=True)


@router.get("/posts/{post_id}/comments", response_model=list[Comment])
async def get_comments_on_post(
    post_id: int, session: AsyncSession = Depends(get_async_session)
):
    # Ensure post exists
    post = await find_post(session, post_id)
    if post is None:
        raise HTTPException(
            status_code=404, detail=f"Post Not Found based on post_id={post_id}"
        )

    query = select(CommentORM).where(CommentORM.post_id == post_id)
    result = await session.execute(query)
    comments = result.scalars().all()
    return [Comment.model_validate(c, from_attributes=True) for c in comments]


@router.get("/posts/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(
    post_id: int, session: AsyncSession = Depends(get_async_session)
):
    # Ensure post exists
    post = await find_post(session, post_id)
    if post is None:
        raise HTTPException(
            status_code=404, detail=f"Post Not Found based on post_id={post_id}"
        )

    query = select(CommentORM).where(CommentORM.post_id == post_id)
    result = await session.execute(query)
    comment_rows = result.scalars().all()
    comments = [Comment.model_validate(c, from_attributes=True) for c in comment_rows]
    return UserPostWithComments(post=post, comments=comments)
