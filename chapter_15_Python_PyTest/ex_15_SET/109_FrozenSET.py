# Frozen Set (Immutable Set)
# A frozenset cannot be changed after creation.
my_list = [1, 2, 3, 3]
fset = frozenset(my_list)
# fset.add(4) AttributeError: 'frozenset' object has no attribute 'add'

print(fset)