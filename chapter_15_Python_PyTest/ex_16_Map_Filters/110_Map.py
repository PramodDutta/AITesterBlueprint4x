numbers = [1, 2, 3, 4, 5]
def sq(x):
    return x**2

# for n in numbers:
#     print(sq(n))

all_sq = list(map(sq, numbers))
print(all_sq)