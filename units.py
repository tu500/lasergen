class Rel():
    def __init__(self, value):
        self.value = value

    def total_length_from_unit(self, unit_length):
        return self.value * unit_length
    def unit_length_from_total(self, total_length):
        return total_length / self.value

    def __add__(self, b):
        return Rel(self.value + b.value)
    def __sub__(self, b):
        return Rel(self.value - b.value)
    def __mul__(self, b):
        return Rel(self.value * b)
    def __div__(self, b):
        return Rel(self.value / b)

    def __iadd__(self, b):
        self.value += b.value
        return self
    def __isub__(self, b):
        self.value -= b.value
        return self
    def __imul__(self, b):
        self.value *= b
        return self
    def __idiv__(self, b):
        self.value /= b
        return self

    def __eq__(self, other):
        return isinstance(other, Rel) and self.value == other.value

    def __repr__(self):
        return 'Rel({})'.format(self.value)

class Frac():
    def __init__(self, value, translate=0):
        self.value = value
        self.translate = translate

    def total_length(self, v):
        return self.value * v + self.translate

    def __add__(self, b):
        return Frac(self.value + b.value, self.translate + b.translate)
    def __sub__(self, b):
        return Frac(self.value - b.value, self.translate - b.translate)
    def __mul__(self, b):
        return Frac(self.value * b, self.translate * b)
    def __div__(self, b):
        return Frac(self.value / b, self.translate / b)

    def __iadd__(self, b):
        self.value += b.value
        self.translate += b.translate
        return self
    def __isub__(self, b):
        self.value -= b.value
        self.translate -= b.translate
        return self
    def __imul__(self, b):
        self.value *= b
        self.translate *= b
        return self
    def __idiv__(self, b):
        self.value /= b
        self.translate /= b
        return self

    def __eq__(self, other):
        return isinstance(other, Frac) and self.value == other.value and self.translate == other.translate

    def __repr__(self):
        return 'Rel({}, {})'.format(self.value, self.translate)
