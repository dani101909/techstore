from decimal import Decimal
    
class Specification:
    def is_satisfied_by(self, order):
        raise NotImplementedError

    def __and__(self, other):
        return AndSpec(self, other)

    def __or__(self, other):
        return OrSpec(self, other)

    def __invert__(self):
        return NotSpec(self)


class AndSpec(Specification):
    def __init__(self, left, right):
        self.left, self.right = left, right

    def is_satisfied_by(self, order):
        return (self.left.is_satisfied_by(order)
                and self.right.is_satisfied_by(order))


class OrSpec(Specification):
    def __init__(self, left, right):
        self.left, self.right = left, right

    def is_satisfied_by(self, order):
        return (self.left.is_satisfied_by(order)
                or self.right.is_satisfied_by(order))


class NotSpec(Specification):
    def __init__(self, spec):
        self.spec = spec

    def is_satisfied_by(self, order):
        return not self.spec.is_satisfied_by(order)

class MinimumAmountSpec(Specification):
    def __init__(self, minimum):
        self.minimum = minimum

    def is_satisfied_by(self, order):
        return order.total.amount > self.minimum   # estricto: > y no >=


class VIPCustomerSpec(Specification):
    def is_satisfied_by(self, order):
        return order.customer.is_vip


class MinimumUnitsSpec(Specification):
    def __init__(self, minimum):
        self.minimum = minimum

    def is_satisfied_by(self, order):
        return order.units >= self.minimum        # al menos 4 unidades


class ActivePromotionSpec(Specification):
    def is_satisfied_by(self, order):
        return order.has_promotion


# Regla de 10 %: VIP, total > 500, al menos 4 unidades y sin promoción
ten_percent = (
    MinimumAmountSpec(Decimal("500"))
    & VIPCustomerSpec()
    & MinimumUnitsSpec(4)
    & ~ActivePromotionSpec()
)

# Regla de 5 %: total > 5000 y sin promoción
five_percent = MinimumAmountSpec(Decimal("5000")) & ~ActivePromotionSpec()

# Cualquiera de las dos reglas da derecho a descuento
any_discount = ten_percent | five_percent


def discount_rate(order):
    """Si se cumplen ambas reglas, gana primero la de 10 %."""
    if ten_percent.is_satisfied_by(order):
        return Decimal("0.10")
    if five_percent.is_satisfied_by(order):
        return Decimal("0.05")
    return Decimal("0")