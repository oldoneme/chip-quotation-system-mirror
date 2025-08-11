"""
统一的异常处理模块
"""
from typing import Any, Optional, Dict
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


class APIException(HTTPException):
    """自定义API异常基类"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class BusinessException(APIException):
    """业务逻辑异常"""
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class NotFoundException(APIException):
    """资源未找到异常"""
    def __init__(self, resource: str):
        super().__init__(status_code=404, detail=f"{resource}未找到")


class ValidationException(APIException):
    """数据验证异常"""
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)


class AuthenticationException(APIException):
    """认证异常"""
    def __init__(self, detail: str = "认证失败"):
        super().__init__(status_code=401, detail=detail)


class PermissionException(APIException):
    """权限异常"""
    def __init__(self, detail: str = "权限不足"):
        super().__init__(status_code=403, detail=detail)


async def api_exception_handler(request: Request, exc: APIException):
    """API异常处理器"""
    logger.error(f"API Exception: {exc.detail}, Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    """Pydantic验证异常处理器"""
    logger.error(f"Validation Error: {exc.errors()}, Path: {request.url.path}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "数据验证失败",
            "errors": exc.errors(),
            "status_code": 422
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"Unexpected error: {str(exc)}, Path: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误，请稍后重试",
            "status_code": 500
        }
    )