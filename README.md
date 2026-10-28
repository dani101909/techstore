# TechStore U4: lógica de negocio de pedidos

Práctica guiada de la Unidad 4 (Componentes de Lógica de Negocio, FIME-UANL).
Administra pedidos de una tienda ficticia con objetos en memoria: lee clientes,
productos y pedidos desde CSV, aplica reglas de descuento con el patrón
Specification, controla el estado de cada pedido con eventos de dominio y
expone operaciones mediante una API REST con FastAPI.

No usa base de datos: al cerrar el programa los cambios se pierden.

## Requisitos
- Python 3.11 o superior

## Instalación
```
python -m venv .venv
# PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

python -m pip install fastapi uvicorn pytest httpx
```

## Ejecución
```
python cargar_csv.py          # carga y muestra los 16 pedidos
python escenarios.py          # ejecuta E01-E15 y genera bitacora.md
python -m pytest -q           # corre las pruebas
uvicorn app.api:app --reload  # levanta la API
```
Documentación interactiva: http://127.0.0.1:8000/docs

## Estructura
```
app/domain.py          Money, Customer, OrderItem, Order, estados y eventos
app/specifications.py  Specification (AND, OR, NOT) y reglas de descuento
app/api.py             API REST con FastAPI
tests/                 Pruebas pytest (dominio y API)
datos/                 CSV de clientes, productos, pedidos y escenarios
cargar_csv.py          Cargador de datos (entregado en el paquete)
escenarios.py          Ejecuta los 15 escenarios y genera la bitácora
bitacora.md            Bitácora de E01-E15
```

## Reglas de negocio
- Money es inmutable, usa Decimal y no admite importes negativos.
- Máximo 20 unidades por pedido (se suman unidades, no renglones).
- Descuento 10 %: cliente VIP, total > 500 MXN, al menos 4 unidades y sin promoción.
- Descuento 5 %: total > 5000 MXN y sin promoción.
- Si se cumplen ambas reglas, aplica primero el 10 %.
- Una promoción activa bloquea cualquier descuento.
- Un pedido solo se confirma si tiene artículos y el cliente está activo.

## Estados y eventos
```
DRAFT --confirm--> CONFIRMED --ship--> SHIPPED --deliver--> DELIVERED
                       |                  |
                    cancel              return
                       |                  |
                   CANCELLED          RETURNED
```
Eventos: OrderConfirmed, OrderShipped, OrderCancelled, OrderDelivered y
OrderReturned. Cada método valida primero, cambia el estado después y registra
el evento al final; una operación inválida no cambia el estado ni agrega eventos.

## Endpoints
- GET /orders/{id}: consulta un pedido (estado, unidades, total, descuento, eventos).
- POST /orders/{id}/confirm: confirma el pedido.
- POST /orders/{id}/ship: envía el pedido. Cuerpo: {"tracking_number": "..."}.
- POST /orders/{id}/cancel: cancela el pedido. Cuerpo: {"reason": "..."}.

Respuestas: 200 correcto, 404 pedido inexistente, 409 transición no permitida
o límite de unidades, 422 datos inválidos (sin artículos, cliente inactivo,
guía o motivo vacío).

## Evidencias
Las capturas están en la carpeta `evidencias/`.