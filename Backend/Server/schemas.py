from pydantic import BaseModel, field_validator

class UserCreate(BaseModel):
    email: str
    password: str

    @field_validator("password")
    def check_length(cls, value):
        if len(value) > 72:
            raise ValueError("Password must be <= 72 characters")
        return value
    


class UserLogin(BaseModel):
    email: str
    password: str

class WorkspaceCreate(BaseModel):
    name: str


class AssistantEmbeddingURLCreate(BaseModel):
    assistant_name: str
    cloudinary_url: str


class AssistantRead(BaseModel):
    id: int
    assistant_id: str
    name: str
    status: str
    source_count: int
    user_email: str
    last_error: str | None = None
    created_at: str
    updated_at: str


class AssistantChatRequest(BaseModel):
    question: str
    top_k: int = 4
