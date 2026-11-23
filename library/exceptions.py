"""Domain errors. Catch ``LibraryError`` to handle any rule violation."""


class LibraryError(Exception):
    """Base class for every business-rule violation."""


class DuplicateError(LibraryError):
    """A book ISBN or member ID is already registered."""


class BookNotFoundError(LibraryError):
    pass


class MemberNotFoundError(LibraryError):
    pass


class NotLendableError(LibraryError):
    """The title exists but may not leave the library (e.g. reference books)."""


class NoCopiesAvailableError(LibraryError):
    pass


class BorrowLimitError(LibraryError):
    """The member already holds as many books as their membership allows."""


class AlreadyBorrowedError(LibraryError):
    """The member already has a copy of this title."""


class OutstandingFinesError(LibraryError):
    """The member must pay their fines before borrowing again."""


class LoanNotFoundError(LibraryError):
    """No active loan matches this book and member."""
