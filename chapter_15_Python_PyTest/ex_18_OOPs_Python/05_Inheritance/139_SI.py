class BaseTest:
    driver = "chrome"
    __driver2 = "firefox"

    def setUp(self):
        print("Base is setup!")

# si -> classSon(classFather)
class LoginTest(BaseTest):
    def run(self):
        self.setUp()
        print("Running TC")


t = LoginTest()
t.run()