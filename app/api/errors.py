from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHttpException

type ErrorDetails = list[dict[str, str]] | dict[str, object] | None


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: ErrorDetails = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def build_error_content(
    code: str,
    message: str,
    details: ErrorDetails = None,
) -> dict[str, dict[str, object]]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }


async def api_error_handler(
    request: Request,
    exception: ApiError,
) -> JSONResponse:
    del request

    return JSONResponse(
        status_code=exception.status_code,
        content=build_error_content(
            code=exception.code,
            message=exception.message,
            details=exception.details,
        ),
    )


async def validation_error_handler(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    del request

    details = [
        {
            "field": ".".join(str(location_part) for location_part in error["loc"]),
            "message": str(error["msg"]),
            "type": str(error["type"]),
        }
        for error in exception.errors()
    ]

    return JSONResponse(
        status_code=422,
        content=build_error_content(
            code="validation_error",
            message="Request validation failed.",
            details=details,
        ),
    )


async def http_error_handler(
    request: Request,
    exception: StarletteHttpException,
) -> JSONResponse:
    del request

    error_codes = {
        404: "not_found",
        405: "method_not_allowed",
    }

    message = (
        exception.detail
        if isinstance(exception.detail, str)
        else "The request could not be processed."
    )

    return JSONResponse(
        status_code=exception.status_code,
        content=build_error_content(
            code=error_codes.get(
                exception.status_code,
                "http_error",
            ),
            message=message,
        ),
    )


def register_exception_handlers(
    application: FastAPI,
) -> None:
    application.add_exception_handler(
        ApiError,
        api_error_handler,
    )
    application.add_exception_handler(
        RequestValidationError,
        validation_error_handler,
    )
    application.add_exception_handler(
        StarletteHttpException,
        http_error_handler,
    )
