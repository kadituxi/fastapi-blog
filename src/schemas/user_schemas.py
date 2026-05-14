from pydantic import ConfigDict, BaseModel, Field, EmailStr


class UserBaseSchema(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(min_length=10, max_length=120)


class UserCreateSchema(UserBaseSchema):
    password: str = Field(min_length=8)


class UserResponseSchema(UserBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_file: str | None
    image_path: str


class UserUpdateSchema(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, min_length=10, max_length=120)
    user_id: int


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(max_length=120)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
