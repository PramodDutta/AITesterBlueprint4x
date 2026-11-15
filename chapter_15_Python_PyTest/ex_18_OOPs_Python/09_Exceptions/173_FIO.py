try:
    data = open("09_Exceptions/test.json").read()
    print(data)
except FileNotFoundError as fnf:
    print(fnf)