def sum_three(a=1, b=1, c=1):
    return a + b + c


result1 = sum_three()
print(result1)

result2 = sum_three(1, 2)
print(result2)

result3 = sum_three(1, 2, 3)
print(result3)

result5 = sum_three(b=67, a=10, c=45)
print(result5)

result6 = sum_three(a=10, b=67, c=45)
print(result6)