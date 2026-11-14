class MathClass:
    def add(self, a, b):
        return a + b

    def add(self, a, b, c=10):
        return a + b + c


obj_ref = MathClass()
print(obj_ref.add(3, 4, 5))
print(obj_ref.add(3.14, 4.14))