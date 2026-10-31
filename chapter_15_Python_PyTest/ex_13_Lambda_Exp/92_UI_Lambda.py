user_input = int(input("Enter the number"))
check_even_odd_f = lambda num: "Even" if num % 2 == 0 else "Odd"
result = check_even_odd_f(user_input)
print(result)

# Alternate in one line
print((lambda num: "Even" if num % 2 == 0 else "Odd")(int(input("Enter the number: "))))



import math
op2 = lambda: math.pow(int(input("Enter the number")), 2)
print(op2())