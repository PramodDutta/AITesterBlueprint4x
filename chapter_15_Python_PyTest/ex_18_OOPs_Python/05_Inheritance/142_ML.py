class TestSuite:
    def info(self):
        print("This is GF - Step 1")


class BaseTest(TestSuite):
    def setup(self):
        print("BaseTest - F - Step 2")


class UITest(BaseTest):
    def run(self):
        self.info()
        self.setup()
        print("Running Test Case")


test = UITest()
test.run()