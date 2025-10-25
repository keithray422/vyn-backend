from pydantic import BaseModel

class UserCreate(BaseModel):
    phone_number: str
    username: str

class UserResponse(BaseModel):
    id: int
    phone_number: str
    username: str

    class Config:
        orm_mode = True
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
