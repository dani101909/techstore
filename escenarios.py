"""Ejecuta los escenarios E01-E15 y genera bitacora.md."""
import csv
from pathlib import Path
from cargar_csv import load_fixture
from app.domain import DomainException, OrderItem, Money
from app.specifications import discount_rate
from decimal import Decimal

BASE = Path(__file__).resolve().parent



EXPLICACIONES = {
    "E01": "O001 es de un cliente VIP, vale 2100.00 (>500), tiene 4 unidades (>=4) y no tiene promoción. Cumple las cuatro condiciones del AND, así que aplica el 10 %.",
    "E02": "El cliente no es VIP, por lo que la regla del 10 % falla, y el total de 1050.00 no supera 5000, por lo que la del 5 % también falla. Resultado: 0 %.",
    "E03": "El cliente C003 es VIP pero está inactivo. confirm() exige cliente activo y lanza InvalidOrderData; el pedido sigue en DRAFT y no se emite evento.",
    "E04": "O005 cumpliría los requisitos del 10 % (VIP, 2100.00, 4 unidades), pero tiene promoción activa. La negación ~ActivePromotionSpec() falla en ambas reglas, por lo que no hay descuento.",
    "E05": "El cliente no es VIP ni tiene 4 unidades, así que no entra al 10 %. Pero el total de 18000.00 supera 5000 y no hay promoción, por lo que entra a la regla alternativa del 5 %.",
    "E06": "El pedido no tiene artículos. confirm() exige al menos un artículo y lanza InvalidOrderData; el estado sigue en DRAFT y no se emite evento.",
    "E07": "20 unidades es exactamente el límite permitido, porque la regla rechaza solo más de 20. El cliente está activo y hay artículos, así que confirma, pasa a CONFIRMED y emite OrderConfirmed.",
    "E08": "O009 ya tiene 19 unidades. Agregar 2 daría 21, que excede el máximo de 20. add_item() valida antes de modificar items, lanza OrderItemLimitExceeded y las unidades se quedan en 19. Se suman unidades, no renglones.",
    "E09": "El total es exactamente 500.00. La regla usa > (estricto), no >=, así que 500 no supera el umbral. Además el cliente no es VIP. Resultado: 0 %.",
    "E10": "El cliente es VIP y el total (1500.00) supera 500, pero solo tiene 3 unidades y se exigen al menos 4. Falla MinimumUnitsSpec(4), así que no hay descuento.",
    "E11": "La confirmación es válida (hay artículos, cliente activo, estado DRAFT). Después, ship() con guía vacía lanza InvalidOrderData; el pedido se queda en CONFIRMED y solo existe el evento OrderConfirmed.",
    "E12": "La primera confirmación pasa de DRAFT a CONFIRMED y emite un evento. La segunda ya no parte de DRAFT, así que lanza InvalidOrderTransition y NO agrega otro evento: se valida primero y se registra al final.",
    "E13": "Tras confirmar y enviar, el pedido está en SHIPPED. cancel() solo permite desde CONFIRMED, por lo que lanza InvalidOrderTransition. El pedido sigue en SHIPPED y no se emite OrderCancelled.",
    "E14": "Cadena válida: DRAFT a CONFIRMED a SHIPPED. return_order() exige SHIPPED, por lo que se ejecuta y el pedido termina en RETURNED con tres eventos en orden.",
    "E15": "Cadena válida: DRAFT a CONFIRMED a SHIPPED. deliver() exige SHIPPED, por lo que se ejecuta y el pedido termina en DELIVERED con tres eventos en orden.",
}

def leer_escenarios():
    with (BASE / "datos" / "escenarios.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def eventos(order):
    return [e.name for e in order.events]


def correr(caso, pedido_id):
    """Devuelve (estado_inicial, operacion, resultado, explicacion, eventos)."""
    order = load_fixture()[pedido_id]      # datos frescos en cada caso
    inicial = order.status.value
    pasos = []

    def intentar(texto, fn):
        try:
            fn()
            pasos.append(f"{texto}: OK")
            return True
        except DomainException as exc:
            pasos.append(f"{texto}: RECHAZADO ({type(exc).__name__}: {exc})")
            return False

    if caso in ("E01", "E02", "E04", "E05", "E09", "E10"):
        tasa = discount_rate(order)
        op = "evaluar_descuento"
        res = (f"Descuento {int(tasa * 100)}% "
               f"(total {order.total.amount}, {order.units} unidades, "
               f"VIP={order.customer.is_vip}, promo={order.has_promotion})")
    elif caso in ("E03", "E06", "E07"):
        op = "confirm()"
        intentar("confirm", order.confirm)
        res = pasos[-1]
    elif caso == "E08":
        op = "add_item(SKU003 x2)"
        intentar("add_item", lambda: order.add_item(
            OrderItem("SKU003", 2, Money(Decimal("120.00")))))
        res = f"{pasos[-1]}; unidades finales: {order.units}"
    elif caso == "E11":
        op = "confirm() y ship('')"
        intentar("confirm", order.confirm)
        intentar("ship sin guía", lambda: order.ship(""))
        res = " | ".join(pasos)
    elif caso == "E12":
        op = "confirm() dos veces"
        intentar("confirm 1", order.confirm)
        intentar("confirm 2", order.confirm)
        res = " | ".join(pasos)
    elif caso == "E13":
        op = "confirm(), ship('GUIA001'), cancel('Cliente lo pidió')"
        intentar("confirm", order.confirm)
        intentar("ship", lambda: order.ship("GUIA001"))
        intentar("cancel", lambda: order.cancel("Cliente lo pidió"))
        res = " | ".join(pasos)
    elif caso == "E14":
        op = "confirm(), ship('GUIA002'), return_order()"
        intentar("confirm", order.confirm)
        intentar("ship", lambda: order.ship("GUIA002"))
        intentar("return_order", order.return_order)
        res = " | ".join(pasos)
    elif caso == "E15":
        op = "confirm(), ship('GUIA003'), deliver()"
        intentar("confirm", order.confirm)
        intentar("ship", lambda: order.ship("GUIA003"))
        intentar("deliver", order.deliver)
        res = " | ".join(pasos)
    else:
        raise ValueError(caso)
    res += f" -> estado final {order.status.value}"
    return inicial, op, res, eventos(order)


if __name__ == "__main__":
    lineas = ["# Bitácora de escenarios E01-E15", ""]
    for esc in leer_escenarios():
        ini, op, res, evs = correr(esc["caso_id"], esc["pedido_id"])
        evtxt = ", ".join(evs) if evs else "ninguno"
        print(f'{esc["caso_id"]} {esc["pedido_id"]} [{ini}] {op}\n    {res}\n    eventos: {evtxt}\n')
        lineas += [
            f'## {esc["caso_id"]} · {esc["pedido_id"]}',
            f"**Estado inicial:** {ini}",
            f"**Operación:** {op}",
            f"**Resultado real:** {res}",
            f'**Objetivo esperado:** {esc["objetivo"]}',
            f'**Explicación:** {EXPLICACIONES[esc["caso_id"]]}',
            f"**Evento emitido:** {evtxt}",
            "",
        ]
    (BASE / "bitacora.md").write_text("\n".join(lineas), encoding="utf-8")
    print("Bitácora guardada en bitacora.md")