from abc import ABC, abstractmethod

class BrowserManger(ABC):
    @abstractmethod
    def start(self):
        pass

    def stop(self):
        print("Stop command, common")

class ChromeBrowser(BrowserManger):
    def start(self):
        # t = ChromeDriver()
        print("We are starting the chrome")

tc = ChromeBrowser()
tc.start()
tc.stop()