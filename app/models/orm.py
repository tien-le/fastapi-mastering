"""SQLAlchemy ORM models using SQLAlchemy 2.0 style."""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Post(Base):
    """Post model representing a user post.

    Attributes:
        id: Primary key identifier
        body: Content of the post
        comments: Related comments for this post
    """

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    body: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy="selectin",  # Eager load comments when loading post
    )


class Comment(Base):
    """Comment model representing a comment on a post.

    Attributes:
        id: Primary key identifier
        body: Content of the comment
        post_id: Foreign key to the associated post
        post: Relationship to the parent post
    """

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    body: Mapped[str | None] = mapped_column(String, nullable=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="comments", lazy="joined")


class User(Base):
    """User model
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    password: Mapped[str | None] = mapped_column(String)
