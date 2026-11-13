
class Car:
    def __init__(self):
        self.public_pramod = "pramod"
        self._protected_baby = "demo123"
        self.__private_baby = "demo123"

    def nany(self):
        self.__password_yogesh_private = "345"

    def wife(self):
        print(self.__private_baby)

    def mother(self):
            print(self.__private_baby)

object_ref = Car()
print(object_ref.public_pramod)
print(object_ref.__private_baby)
# object_ref.wife()
# object_ref.mother()