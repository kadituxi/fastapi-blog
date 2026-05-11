from datetime import datetime

from pydantic import ConfigDict, BaseModel, Field

from schemas.user_schemas import UserResponseSchema


class PostBaseSchema(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    content: str = Field(min_length=10)


class PostCreateSchema(PostBaseSchema):
    pass


class PostUpdateSchema(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=100)
    content: str | None = Field(default=None, min_length=10)
    user_id: int


class PostResponseSchema(PostBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    author: UserResponseSchema
