class Person:
    name = None
    age = None
    phone = None
    occupation = None

    def __init__(self):
        print("Let's take the user input, Please share the name,age,phone,occ")
        self.name = input("Enter the name\n")
        self.age = input("Enter the age\n")
        self.phone = input("Enter the Phone\n")
        self.occupation = input("Enter the occupation\n")

    def display_values(self):
        print("Name is ", self.name, "Age is ", self.age, "Phone is", self.phone, "occupation", self.occupation)

amit = Person()
amit.display_values()