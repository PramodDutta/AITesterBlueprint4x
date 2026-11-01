a = {1, 2, 3}
b = {3, 4, 5}

print(a | b)
print(a.union(b))

print(a & b)            # {3}
print(a.intersection(b))


print(a - b)