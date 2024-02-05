from typing import Any, Protocol


class RequestError(Exception):
    pass


class Converter(Protocol):
    def get_conversion(
        self, from_symbol: str, to_symbol: str, amount: float
    ) -> dict[str, Any]:
        pass
