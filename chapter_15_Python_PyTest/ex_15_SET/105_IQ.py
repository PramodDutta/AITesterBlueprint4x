t = ("TheTestingAcademy", "for", "TheTestingAcademy")
print(t)
print(set(t))

empty = set()
print(type(empty))


mixed = {1, "QA", True, 3.5}
for item in mixed:
    print(item)

mixed.add(10)
print(mixed)
mixed.remove(10)
print(mixed)