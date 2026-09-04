from typing import Any, Dict, Optional
from uuid import uuid4


class AppError(Exception):
    code: str = "INTERNAL_ERROR"
    message: str = "An internal error occurred."
    status_code: int = 500
    details: Optional[Dict[str, Any]] = None

    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        if details is not None:
            self.details = details
        super().__init__(self.message)

    def to_dict(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details or {},
                "request_id": request_id or f"req_{uuid4().hex[:12]}",
            }
        }


class InvalidURLError(AppError):
    code = "INVALID_COURSE_URL"
    message = "The course URL is invalid."
    status_code = 400


class ExtractionError(AppError):
    code = "CONTENT_EXTRACTION_FAILED"
    message = "Failed to extract content from the provided source."
    status_code = 500


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    message = "Input validation failed."
    status_code = 422


class NotFoundError(AppError):
    code = "NOT_FOUND"
    message = "The requested resource was not found."
    status_code = 404


class AIServiceError(AppError):
    code = "AI_SERVICE_ERROR"
    message = "AI service call failed."
    status_code = 502


class RenderingError(AppError):
    code = "RENDERING_ERROR"
    message = "Failed to render presentation."
    status_code = 500


class QAError(AppError):
    code = "QA_FAILED"
    message = "Quality assurance check did not pass."
    status_code = 500


class JobStateError(AppError):
    code = "INVALID_JOB_STATE"
    message = "Invalid job state transition."
    status_code = 409
