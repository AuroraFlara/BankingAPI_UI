from fastapi import HTTPException


class APIError(HTTPException):
    def __init__(self, status_code: int, message: str):
        super().__init__(status_code=status_code, detail={"error": message})


class ValidationAPIError(HTTPException):
    def __init__(self, status_code: int, errors: dict[str, str]):
        super().__init__(status_code=status_code, detail={"errors": errors})
