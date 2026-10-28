from decimal import Decimal

import pytest

from app.domain import (
    Customer,
    InvalidOrderData,
    InvalidOrderTransition,
    Money,
    Order,
    OrderItem,
    OrderItemLimitExceeded,
    OrderStatus,
)
from app.specifications import (
    ActivePromotionSpec,
    MinimumAmountSpec,
    VIPCustomerSpec,
    discount_rate,
    five_percent,
    ten_percent,
)
from cargar_csv import load_fixture


# ---------- Money y OrderItem ----------

def test_money_negativo():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("-1"))


def test_money_no_finito():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("NaN"))


def test_money_add_monedas_distintas():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("1"), "MXN").add(Money(Decimal("1"), "USD"))


def test_money_add_devuelve_objeto_nuevo():
    a, b = Money(Decimal("10.50")), Money(Decimal("4.50"))
    resultado = a.add(b)
    assert resultado.amount == Decimal("15.00")
    assert a.amount == Decimal("10.50")  # el original no cambia


@pytest.mark.parametrize("cantidad", [0, -1])
def test_orderitem_cantidad_invalida(cantidad):
    with pytest.raises(InvalidOrderData):
        OrderItem("SKU001", cantidad, Money(Decimal("600.00")))


def test_orderitem_subtotal_calculado():
    item = OrderItem("SKU001", 2, Money(Decimal("600.00")))
    assert item.subtotal.amount == Decimal("1200.00")


# ---------- Carga de datos ----------

def test_pedido_o001_inicia_draft():
    orders = load_fixture()
    assert orders["O001"].status.value == "DRAFT"
    assert orders["O001"].units == 4
    assert orders["O001"].total.amount == Decimal("2100.00")


def test_se_cargan_16_pedidos_en_draft():
    orders = load_fixture()
    assert len(orders) == 16
    assert all(o.status == OrderStatus.DRAFT for o in orders.values())


# ---------- Límite de unidades ----------

def test_20_unidades_exactas_permitidas():
    assert load_fixture()["O008"].units == 20


def test_21_unidades_rechazadas_y_pedido_no_cambia():
    order = load_fixture()["O009"]          # ya tiene 19
    with pytest.raises(OrderItemLimitExceeded):
        order.add_item(OrderItem("SKU003", 2, Money(Decimal("120.00"))))
    assert order.units == 19
    assert len(order.items) == 1


def test_no_se_agregan_articulos_si_no_es_draft():
    order = load_fixture()["O013"]
    order.confirm()
    with pytest.raises(InvalidOrderTransition):
        order.add_item(OrderItem("SKU003", 1, Money(Decimal("120.00"))))


# ---------- Confirmación ----------

def test_cliente_inactivo_no_confirma():
    order = load_fixture()["O003"]
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.status == OrderStatus.DRAFT
    assert order.events == []


def test_pedido_vacio_no_confirma():
    order = load_fixture()["O007"]
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.status == OrderStatus.DRAFT
    assert order.events == []


def test_confirmacion_doble_no_agrega_evento():
    order = load_fixture()["O013"]
    order.confirm()
    assert order.status == OrderStatus.CONFIRMED
    assert [e.name for e in order.events] == ["OrderConfirmed"]
    with pytest.raises(InvalidOrderTransition):
        order.confirm()
    assert [e.name for e in order.events] == ["OrderConfirmed"]


# ---------- Envío, cancelación, entrega y devolución ----------

@pytest.mark.parametrize("guia", ["", "   "])
def test_envio_sin_guia_rechazado(guia):
    order = load_fixture()["O012"]
    order.confirm()
    with pytest.raises(InvalidOrderData):
        order.ship(guia)
    assert order.status == OrderStatus.CONFIRMED
    assert [e.name for e in order.events] == ["OrderConfirmed"]


def test_no_se_envia_desde_draft():
    order = load_fixture()["O012"]
    with pytest.raises(InvalidOrderTransition):
        order.ship("GUIA001")
    assert order.events == []


def test_cancelacion_desde_shipped_rechazada():
    order = load_fixture()["O014"]
    order.confirm()
    order.ship("GUIA001")
    with pytest.raises(InvalidOrderTransition):
        order.cancel("Cliente lo pidió")
    assert order.status == OrderStatus.SHIPPED
    assert [e.name for e in order.events] == ["OrderConfirmed", "OrderShipped"]


def test_cancelacion_desde_confirmed_con_motivo():
    order = load_fixture()["O002"]
    order.confirm()
    order.cancel("Cliente lo pidió")
    assert order.status == OrderStatus.CANCELLED
    assert order.events[-1].name == "OrderCancelled"


def test_cancelacion_sin_motivo_rechazada():
    order = load_fixture()["O002"]
    order.confirm()
    with pytest.raises(InvalidOrderData):
        order.cancel("  ")
    assert order.status == OrderStatus.CONFIRMED


def test_devolucion_desde_shipped():
    order = load_fixture()["O015"]
    order.confirm()
    order.ship("GUIA002")
    order.return_order()
    assert order.status == OrderStatus.RETURNED
    assert [e.name for e in order.events] == [
        "OrderConfirmed", "OrderShipped", "OrderReturned"]


def test_entrega_desde_shipped():
    order = load_fixture()["O016"]
    order.confirm()
    order.ship("GUIA003")
    order.deliver()
    assert order.status == OrderStatus.DELIVERED
    assert [e.name for e in order.events] == [
        "OrderConfirmed", "OrderShipped", "OrderDelivered"]


def test_no_se_entrega_ni_devuelve_desde_confirmed():
    order = load_fixture()["O016"]
    order.confirm()
    with pytest.raises(InvalidOrderTransition):
        order.deliver()
    with pytest.raises(InvalidOrderTransition):
        order.return_order()
    assert order.status == OrderStatus.CONFIRMED


# ---------- Descuentos y Specifications ----------

def test_descuento_vip_10_por_ciento():
    order = load_fixture()["O001"]
    assert ten_percent.is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0.10")


def test_descuento_5_por_ciento_total_mayor_a_5000():
    order = load_fixture()["O006"]
    assert not ten_percent.is_satisfied_by(order)
    assert five_percent.is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0.05")


def test_promocion_activa_bloquea_descuentos():
    order = load_fixture()["O005"]
    assert discount_rate(order) == Decimal("0")


def test_umbral_500_es_estricto():
    order = load_fixture()["O010"]
    assert order.total.amount == Decimal("500.00")
    assert not MinimumAmountSpec(Decimal("500")).is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0")


def test_vip_con_3_unidades_sin_descuento():
    order = load_fixture()["O011"]
    assert order.units == 3
    assert discount_rate(order) == Decimal("0")


def test_no_vip_sin_descuento():
    assert discount_rate(load_fixture()["O002"]) == Decimal("0")


def test_prioridad_10_sobre_5_cuando_ambas_aplican():
    order = Order(customer=Customer("CX", is_vip=True), id="OX")
    order.add_item(OrderItem("SKU005", 5, Money(Decimal("3200.00"))))  # 16000, 5 u.
    assert ten_percent.is_satisfied_by(order)
    assert five_percent.is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0.10")


def test_composicion_and_or_not():
    order = load_fixture()["O005"]            # VIP con promoción
    vip, promo = VIPCustomerSpec(), ActivePromotionSpec()
    assert (vip & promo).is_satisfied_by(order)
    assert (vip | ~promo).is_satisfied_by(order)
    assert not (~vip | ~promo).is_satisfied_by(order)
    assert not (~promo).is_satisfied_by(order)


def test_specification_no_modifica_el_pedido():
    order = load_fixture()["O001"]
    antes = (order.status, order.units, order.total.amount, len(order.events))
    discount_rate(order)
    assert antes == (order.status, order.units, order.total.amount, len(order.events))