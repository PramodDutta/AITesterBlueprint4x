class BaseTest:
    def run(self):
        print("Running the Base Test")

class LoginTest(BaseTest):
    def run(self):
        print("Runnning Login Test")


t = BaseTest()
# t = LoginTest()
t.run()