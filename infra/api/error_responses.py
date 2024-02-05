from fastapi.responses import JSONResponse


def create_bad_request_response(message: str) -> JSONResponse:
    return JSONResponse(status_code=400, content={"message": message})


def create_forbidden_response(message: str) -> JSONResponse:
    return JSONResponse(status_code=403, content={"message": message})


def create_not_found_response(message: str) -> JSONResponse:
    return JSONResponse(status_code=404, content={"message": message})


def create_conflict_response(message: str) -> JSONResponse:
    return JSONResponse(status_code=409, content={"message": message})
