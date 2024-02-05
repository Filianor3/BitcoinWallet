class BadRequestError(Exception):
    pass


class ForbiddenError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class ExistsError(ConflictError):
    pass


class DoesNotExistError(NotFoundError):
    pass


class UserExistsError(ExistsError):
    pass


class UserDoesNotExistError(DoesNotExistError):
    pass


class WalletExistsError(ExistsError):
    pass


class WalletDoesNotExistError(DoesNotExistError):
    pass


class TransactionExistsError(ExistsError):
    pass


class TransactionDoesNotExistError(DoesNotExistError):
    pass


class WalletLimitError(ConflictError):
    pass


class WalletOwnershipError(ForbiddenError):
    pass


class InsufficientBalanceError(ConflictError):
    pass


class SruliSigije(Exception):
    pass
