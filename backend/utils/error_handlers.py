class DatabaseError(Exception):
    def __init__(self, message: str = "Database operation failed"):
        self.message = message
        self.status_code = 500

class InternalServerError(Exception):
    def __init__(self, message: str = "Something went wrong"):
        self.message = message
        self.status_code = 500