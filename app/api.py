from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from cargar_csv import load_fixture
from app.domain import (
    DomainException,
    InvalidOrderData,
    InvalidOrderTransition,
    OrderItemLimitExceeded,
)
from app.specifications import discount_rate

app = FastAPI(title="TechStore U4")

# Repositorio en memoria: se carga al iniciar y se pierde al cerrar.
orders = load_fixture()


class ShipRequest(BaseModel):
    tracking_number: str


class CancelRequest(BaseModel):
    reason: str


def get_order_or_404(order_id: str):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No existe")
    return order


def run_domain_action(action):
    """Ejecuta una operación del dominio y traduce sus excepciones a HTTP."""
    try:
        action()
    except (InvalidOrderTransition, OrderItemLimitExceeded) as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InvalidOrderData as exc:
        raise HTTPException(status_code=422, detail=str(exc))


def order_summary(order):
    return {"id": order.id, "status": order.status.value}


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = get_order_or_404(order_id)
    return {
        "id": order.id,
        "customer_id": order.customer.id,
        "status": order.status.value,
        "units": order.units,
        "total": str(order.total.amount),
        "currency": order.total.currency,
        "has_promotion": order.has_promotion,
        "discount_rate": str(discount_rate(order)),
        "events": [e.name for e in order.events],
    }


@app.post("/orders/{order_id}/confirm")
def confirm_order(order_id: str):
    order = get_order_or_404(order_id)
    run_domain_action(order.confirm)
    return order_summary(order)


@app.post("/orders/{order_id}/ship")
def ship_order(order_id: str, body: ShipRequest):
    order = get_order_or_404(order_id)
    run_domain_action(lambda: order.ship(body.tracking_number))
    return order_summary(order)


@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str, body: CancelRequest):
    order = get_order_or_404(order_id)
    run_domain_action(lambda: order.cancel(body.reason))
    return order_summary(order)