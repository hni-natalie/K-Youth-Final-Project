class AppException(Exception):
    def __init__(self, detail: str, status_code: int):
        self.detail = detail
        self.status_code = status_code


class DatabaseError(AppException):
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(detail, 500)


class UnprocessableEntityError(AppException):
    def __init__(self, detail: str = "Unprocessable Entity"):
        super().__init__(detail, 422)


class InternalServerError(AppException):
    def __init__(self, detail: str = "Internal Server Error"):
        super().__init__(detail, 500)