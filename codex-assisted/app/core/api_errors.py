from dataclasses import dataclass


@dataclass(slots=True)
class ApiError(Exception):
    status_code: int
    payload: dict
