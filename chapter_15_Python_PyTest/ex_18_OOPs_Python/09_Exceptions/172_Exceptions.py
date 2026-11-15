# Create a Class for the Custom Exception

class InvalidAgeException(Exception):
    pass

def can_you_drink(age):
    if age < 18:
        raise InvalidAgeException("You can't drink!")
    else:
        print("You can drink!")

# can_you_drink(17)
can_you_drink(25)