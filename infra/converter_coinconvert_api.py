from typing import Any

import httpx

from core.converter import Converter, RequestError


class CoinConvertConverter(Converter):
    def get_conversion(
        self, from_symbol: str, to_symbol: str, amount: float
    ) -> dict[str, Any]:
        url = f"https://api.coinconvert.net/convert/{from_symbol}/{to_symbol}"
        params = {"amount": amount}
        trans_response = dict()

        try:
            trans_response = httpx.get(url, params=params).json()
            return trans_response

        except RequestError:
            print("invalid request")

        return trans_response
