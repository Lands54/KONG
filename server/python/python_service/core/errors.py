from typing import Optional, Any, Dict

class PrismError(Exception):
    """
    PRISM Base Exception
    """
    def __init__(
        self, 
        message: str, 
        code: str = "INTERNAL_ERROR", 
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }

class PrismAuthError(PrismError):
    """Authentication failed (e.g. invalid API Key)"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Any] = None):
        super().__init__(message, code="AUTH_FAILED", status_code=401, details=details)

class PrismRateLimitError(PrismError):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Any] = None):
        super().__init__(message, code="RATE_LIMIT", status_code=429, details=details)

class PrismNetworkError(PrismError):
    """Network connection issues"""
    def __init__(self, message: str = "Network error", details: Optional[Any] = None):
        super().__init__(message, code="NETWORK_ERROR", status_code=503, details=details)

class PrismValidationError(PrismError):
    """Invalid input parameters"""
    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(message, code="VALIDATION_ERROR", status_code=422, details=details)
