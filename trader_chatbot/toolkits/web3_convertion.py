from decimal import Decimal


def from_bigint_to_decimal(bigINt: int, decimals: int):
    decimal_number = Decimal(bigINt) / Decimal(10**decimals)
    return decimal_number.__float__()
