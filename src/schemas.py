from datetime import datetime

from pydantic import ConfigDict, BaseModel, Field, EmailStr


class UserBaseSchema(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(min_length=10, max_length=120)


class UserCreateSchema(UserBaseSchema):
    pass


class UserResponseSchema(UserBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_file: str | None
    image_path: str


class PostBaseSchema(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    content: str = Field(min_length=10)


class PostCreateSchema(PostBaseSchema):
    user_id: int


class PostResponseSchema(PostBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    author: UserResponseSchema
