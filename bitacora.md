# Bitácora de escenarios E01-E15

## E01 · O001
**Estado inicial:** DRAFT
**Operación:** evaluar_descuento
**Resultado real:** Descuento 10% (total 2100.00, 4 unidades, VIP=True, promo=False) -> estado final DRAFT
**Objetivo esperado:** 10%
**Explicación:** O001 es de un cliente VIP, vale 2100.00 (>500), tiene 4 unidades (>=4) y no tiene promoción. Cumple las cuatro condiciones del AND, así que aplica el 10 %.
**Evento emitido:** ninguno

## E02 · O002
**Estado inicial:** DRAFT
**Operación:** evaluar_descuento
**Resultado real:** Descuento 0% (total 1050.00, 2 unidades, VIP=False, promo=False) -> estado final DRAFT
**Objetivo esperado:** 0%
**Explicación:** El cliente no es VIP, por lo que la regla del 10 % falla, y el total de 1050.00 no supera 5000, por lo que la del 5 % también falla. Resultado: 0 %.
**Evento emitido:** ninguno

## E03 · O003
**Estado inicial:** DRAFT
**Operación:** confirm()
**Resultado real:** confirm: RECHAZADO (InvalidOrderData: Requiere artículos y cliente activo) -> estado final DRAFT
**Objetivo esperado:** rechazo
**Explicación:** El cliente C003 es VIP pero está inactivo. confirm() exige cliente activo y lanza InvalidOrderData; el pedido sigue en DRAFT y no se emite evento.
**Evento emitido:** ninguno

## E04 · O005
**Estado inicial:** DRAFT
**Operación:** evaluar_descuento
**Resultado real:** Descuento 0% (total 2100.00, 4 unidades, VIP=True, promo=True) -> estado final DRAFT
**Objetivo esperado:** 0%
**Explicación:** O005 cumpliría los requisitos del 10 % (VIP, 2100.00, 4 unidades), pero tiene promoción activa. La negación ~ActivePromotionSpec() falla en ambas reglas, por lo que no hay descuento.
**Evento emitido:** ninguno

## E05 · O006
**Estado inicial:** DRAFT
**Operación:** evaluar_descuento
**Resultado real:** Descuento 5% (total 18000.00, 1 unidades, VIP=False, promo=False) -> estado final DRAFT
**Objetivo esperado:** 5%
**Explicación:** El cliente no es VIP ni tiene 4 unidades, así que no entra al 10 %. Pero el total de 18000.00 supera 5000 y no hay promoción, por lo que entra a la regla alternativa del 5 %.
**Evento emitido:** ninguno

## E06 · O007
**Estado inicial:** DRAFT
**Operación:** confirm()
**Resultado real:** confirm: RECHAZADO (InvalidOrderData: Requiere artículos y cliente activo) -> estado final DRAFT
**Objetivo esperado:** rechazo
**Explicación:** El pedido no tiene artículos. confirm() exige al menos un artículo y lanza InvalidOrderData; el estado sigue en DRAFT y no se emite evento.
**Evento emitido:** ninguno

## E07 · O008
**Estado inicial:** DRAFT
**Operación:** confirm()
**Resultado real:** confirm: OK -> estado final CONFIRMED
**Objetivo esperado:** exito
**Explicación:** 20 unidades es exactamente el límite permitido, porque la regla rechaza solo más de 20. El cliente está activo y hay artículos, así que confirma, pasa a CONFIRMED y emite OrderConfirmed.
**Evento emitido:** OrderConfirmed

## E08 · O009
**Estado inicial:** DRAFT
**Operación:** add_item(SKU003 x2)
**Resultado real:** add_item: RECHAZADO (OrderItemLimitExceeded: Máximo 20 unidades); unidades finales: 19 -> estado final DRAFT
**Objetivo esperado:** rechazo
**Explicación:** O009 ya tiene 19 unidades. Agregar 2 daría 21, que excede el máximo de 20. add_item() valida antes de modificar items, lanza OrderItemLimitExceeded y las unidades se quedan en 19. Se suman unidades, no renglones.
**Evento emitido:** ninguno

## E09 · O010
**Estado inicial:** DRAFT
**Operación:** evaluar_descuento
**Resultado real:** Descuento 0% (total 500.00, 2 unidades, VIP=False, promo=False) -> estado final DRAFT
**Objetivo esperado:** 0%
**Explicación:** El total es exactamente 500.00. La regla usa > (estricto), no >=, así que 500 no supera el umbral. Además el cliente no es VIP. Resultado: 0 %.
**Evento emitido:** ninguno

## E10 · O011
**Estado inicial:** DRAFT
**Operación:** evaluar_descuento
**Resultado real:** Descuento 0% (total 1500.00, 3 unidades, VIP=True, promo=False) -> estado final DRAFT
**Objetivo esperado:** 0%
**Explicación:** El cliente es VIP y el total (1500.00) supera 500, pero solo tiene 3 unidades y se exigen al menos 4. Falla MinimumUnitsSpec(4), así que no hay descuento.
**Evento emitido:** ninguno

## E11 · O012
**Estado inicial:** DRAFT
**Operación:** confirm() y ship('')
**Resultado real:** confirm: OK | ship sin guía: RECHAZADO (InvalidOrderData: Se requiere número de guía) -> estado final CONFIRMED
**Objetivo esperado:** rechazo envio
**Explicación:** La confirmación es válida (hay artículos, cliente activo, estado DRAFT). Después, ship() con guía vacía lanza InvalidOrderData; el pedido se queda en CONFIRMED y solo existe el evento OrderConfirmed.
**Evento emitido:** OrderConfirmed

## E12 · O013
**Estado inicial:** DRAFT
**Operación:** confirm() dos veces
**Resultado real:** confirm 1: OK | confirm 2: RECHAZADO (InvalidOrderTransition: Solo DRAFT) -> estado final CONFIRMED
**Objetivo esperado:** rechazo segunda
**Explicación:** La primera confirmación pasa de DRAFT a CONFIRMED y emite un evento. La segunda ya no parte de DRAFT, así que lanza InvalidOrderTransition y NO agrega otro evento: se valida primero y se registra al final.
**Evento emitido:** OrderConfirmed

## E13 · O014
**Estado inicial:** DRAFT
**Operación:** confirm(), ship('GUIA001'), cancel('Cliente lo pidió')
**Resultado real:** confirm: OK | ship: OK | cancel: RECHAZADO (InvalidOrderTransition: Solo CONFIRMED puede cancelarse) -> estado final SHIPPED
**Objetivo esperado:** rechazo cancelacion
**Explicación:** Tras confirmar y enviar, el pedido está en SHIPPED. cancel() solo permite desde CONFIRMED, por lo que lanza InvalidOrderTransition. El pedido sigue en SHIPPED y no se emite OrderCancelled.
**Evento emitido:** OrderConfirmed, OrderShipped

## E14 · O015
**Estado inicial:** DRAFT
**Operación:** confirm(), ship('GUIA002'), return_order()
**Resultado real:** confirm: OK | ship: OK | return_order: OK -> estado final RETURNED
**Objetivo esperado:** exito
**Explicación:** Cadena válida: DRAFT a CONFIRMED a SHIPPED. return_order() exige SHIPPED, por lo que se ejecuta y el pedido termina en RETURNED con tres eventos en orden.
**Evento emitido:** OrderConfirmed, OrderShipped, OrderReturned

## E15 · O016
**Estado inicial:** DRAFT
**Operación:** confirm(), ship('GUIA003'), deliver()
**Resultado real:** confirm: OK | ship: OK | deliver: OK -> estado final DELIVERED
**Objetivo esperado:** exito
**Explicación:** Cadena válida: DRAFT a CONFIRMED a SHIPPED. deliver() exige SHIPPED, por lo que se ejecuta y el pedido termina en DELIVERED con tres eventos en orden.
**Evento emitido:** OrderConfirmed, OrderShipped, OrderDelivered
