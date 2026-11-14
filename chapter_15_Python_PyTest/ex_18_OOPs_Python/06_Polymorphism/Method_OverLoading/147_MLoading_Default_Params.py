class Person:
    def say_name(self, name):
        print("Hi", name)

    def say_name(self, name, lastname="Dutta"):
        print("Hi,", name, lastname)


t = Person()
t.say_name("Dutta")

t = Person()
t.say_name("Pramod", "Sharma")