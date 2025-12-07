"""Models Module"""
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, ForeignKey, Integer, String


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Post(Base):
    """Table: posts"""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    body = Column(String, nullable=True)

    # ORM relationship (no Mapped[] needed)
    comments = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )


class Comment(Base):
    """Table: comments"""

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    body = Column(String, nullable=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)

    # Relationship back to Post
    post = relationship("Post", back_populates="comments")
