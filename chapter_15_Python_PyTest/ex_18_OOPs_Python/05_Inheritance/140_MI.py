class APIBase:
    def api_auth(self):
        print("Authenticatin API")

class DBBase:
    def db_connect(self):
        print("Connecting to the DB")


class TestHybrid(APIBase, DBBase):
    def run(self):
        self.api_auth()
        self.db_connect()
        print("Test Case Running.")

tc1 = TestHybrid()
tc1.run()