from string import hexdigits
from pydantic import BaseModel, PositiveInt, field_validator, ValidationInfo, Field


def check_common_ids(_id: str, info: ValidationInfo) -> str:
    if not all([c in hexdigits.lower() for c in _id]) or len(_id) != 24:
        raise ValueError(f'{info.field_name} must be a 24-character hex string')
    return _id



class Cart(BaseModel):
    uid: str
    pid: str
    quantity: PositiveInt

    validate_fields = field_validator('uid', 'pid')(check_common_ids)


class Order(BaseModel):
    uid: str
    promocodes: list[str]
    pay_timeout: int = Field(ge=0)

    validate_fields = field_validator('uid')(check_common_ids)


class PayData(BaseModel):
    oid: str
    pay_system: str

    validate_fields = field_validator('oid')(check_common_ids)


class ProductReturn(BaseModel):
    pid: str
    quantity: PositiveInt

    validate_fields = field_validator('pid')(check_common_ids)
