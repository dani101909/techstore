from cargar_csv import load_fixture
from app.domain import InvalidOrderTransition

orders = load_fixture()
order = orders["O013"]

print(order.status, [e.name for e in order.events])
order.confirm()
print(order.status, [e.name for e in order.events])

try:
    order.confirm()
except InvalidOrderTransition as exc:
    print("Rechazado:", exc)

print(order.status, [e.name for e in order.events])