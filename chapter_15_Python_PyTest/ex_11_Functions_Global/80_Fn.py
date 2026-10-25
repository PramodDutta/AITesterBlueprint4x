pb_global_b = 12

def my_function():
    pb_a = 10
    print(pb_a)
    print(pb_global_b)


print(pb_global_b)
# print(pb_a) # NameError: name 'pb_a' is not defined
my_function()