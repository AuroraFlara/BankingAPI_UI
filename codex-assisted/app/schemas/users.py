from app.schemas.common import StrictCamelModel


class RegisterRequest(StrictCamelModel):
    name: str
    email: str
    password: str
    address: str
    phone_number: str
    country_code: str


class LoginRequest(StrictCamelModel):
    identifier: str
    password: str


class LoginResponse(StrictCamelModel):
    token: str
