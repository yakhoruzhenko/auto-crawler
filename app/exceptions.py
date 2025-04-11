class ReviewAlreadyExists(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class FailedToFetchView(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)
