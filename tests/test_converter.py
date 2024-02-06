# import pytest
# import vcr

from core.converter import RequestError
from infra.converter_coinconvert_api import CoinConvertConverter

# Create a VCR instance
# my_vcr = vcr.VCR(cassette_library_dir="cassettes")


# Test case for converting one Bitcoin to dollars
# @my_vcr.use_cassette()
def test_convert_bitcoin_to_dollars() -> None:
    converter = CoinConvertConverter()

    # Specify the conversion parameters
    from_symbol = "BTC"
    to_symbol = "USD"
    amount = 1.0  # Convert one Bitcoin

    try:
        # Call the method of the converter
        conversion_result = converter.get_conversion(from_symbol, to_symbol, amount)
        assert isinstance(
            conversion_result, dict
        ), "Conversion result should be a dictionary"
        assert (
            conversion_result["status"] == "success"
        ), "Conversion result status is not success"
        assert (
            conversion_result[from_symbol] > 0
        ), "Converted amount should be greater than 0"
        assert (
            conversion_result[to_symbol] > 0
        ), "Conversion rate should be greater than 0"

    except RequestError:
        # Handle the case where the request to the external API fails
        assert False, "Request to external API failed"
