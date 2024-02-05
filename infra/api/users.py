from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.errors import UserExistsError
from infra.api.dependables import UserServiceDependable
from infra.api.error_responses import (
    create_bad_request_response,
    create_conflict_response,
)

user_api = APIRouter(tags=["Users"])


class CreateUserRequest(BaseModel):
    email: str
    password: str


class CreateUserResponse(BaseModel):
    api_key: UUID


@user_api.post(
    "/users", status_code=status.HTTP_201_CREATED, response_model=CreateUserResponse
)
def register_user(
    request: CreateUserRequest, user_service: UserServiceDependable
) -> CreateUserResponse | JSONResponse:
    try:
        created_user = user_service.register_user(request.email, request.password)
        return CreateUserResponse(api_key=created_user.api_key)

    except ValueError as validation_error:
        return create_bad_request_response(str(validation_error))
    except UserExistsError as user_exists_error:
        return create_conflict_response(str(user_exists_error))
