class Dog:
    # A
    name = None
    breed = None
    height = None
    weight = None
    # B
    def bark(self):
        print("Barking")
        # print(name)
        print(self.name)

    def talk(self):
        print("Talking")


chow = Dog()

# Dog() - Object
# chow -> Object Ref