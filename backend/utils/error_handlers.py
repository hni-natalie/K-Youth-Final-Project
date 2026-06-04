class DatabaseError(Exception):
    def __init__(self, detail: str = "Database operation failed"):
        self.detail = detail
        self.status_code = 500

class InternalServerError(Exception):
    def __init__(self, detail: str = "Something went wrong"):
        self.detail = detail
        self.status_code = 500