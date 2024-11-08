import uuid
from datetime import datetime as dt


def send_payment(oid: str,
                 pay_summ: float,
                 pay_system: str) -> dict:

    pay_id = uuid.uuid4().hex
    result = {'pay_id': pay_id,
              'order_id': oid,
              'pay_date': str(dt.now().isoformat()),
              'pay_sum': pay_summ,
              'pay_system': pay_system,
              'pay_status': 'Successful'}

    return result


def return_payment(pay_id: str,
                   pay_summ: float,
                   pay_system: str) -> dict:
    pay_return_date = str(dt.now().isoformat())
    return {'pay_id': pay_id,
            'pay_sum': pay_summ,
            'pay_system': pay_system,
            'pay_return_date': pay_return_date,
            'pay_status': 'Successful'}
