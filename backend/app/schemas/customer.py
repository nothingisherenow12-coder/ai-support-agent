from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: str = Field(
        min_length=3,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    company: str | None = Field(default=None, max_length=255)

class CustomerResponse(BaseModel):
    id:int
    name:str
    email:str
    company:str| None=None

    model_config={
        "from_attributes":True
    }


class CustomerPage(BaseModel):
    items: list[CustomerResponse]
    total: int
    limit: int
    offset: int
