def outer_function():
    var1 = 30 # local

    def inner_function():
        var2 = 90
        print(var1)

    def inner_function2():
        var1 = 100
        print(var1)
        # print(var2)


    inner_function()
    inner_function2()

outer_function()