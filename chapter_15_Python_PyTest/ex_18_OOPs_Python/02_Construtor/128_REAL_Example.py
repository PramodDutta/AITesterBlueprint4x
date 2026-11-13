class Calc:
    a = None
    b = None

    def __init__(self):
        print("DC")

    def sum(self, a, b):
        return a+b
    
    def sub(self, a, b):
        return a - b

    def mul(self, a, b):
        return a * b

    def div(self, a, b):
        return a / b

a = float(input("Enter the value of a"))
b = float(input("Enter the value of b"))

object_ref = Calc()

output_sum = object_ref.sum(a, b)
output_sub = object_ref.sub(a, b)
output_mul = object_ref.mul(a, b)
output_div = object_ref.div(a, b)
print(output_sum, output_sub, output_mul, output_div)