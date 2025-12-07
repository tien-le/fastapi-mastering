from pydantic import BaseModel, ConfigDict


# User Post
class UserPostIn(BaseModel):
    body: str


class UserPost(UserPostIn):
    id: int

    # To enable ORM mode, or access to attributes using dot notation,
    # we might add a configuration dictionary with "from_attributes=True"
    model_config = ConfigDict(from_attributes=True)


# User Comment
class CommentIn(BaseModel):
    body: str
    post_id: int


class Comment(CommentIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserPostWithComments(BaseModel):
    post: UserPost
    comments: list[Comment]
