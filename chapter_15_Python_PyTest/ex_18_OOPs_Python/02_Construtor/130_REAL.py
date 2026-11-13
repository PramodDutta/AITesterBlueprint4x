class Baby:
    name : None

    def __init__(self, nameGiven):
        self.name = nameGiven

    def printName(self):
        print(self.name)


b = Baby("gugu")
b2 = Baby("sema")
b.printName()
b2.printName()