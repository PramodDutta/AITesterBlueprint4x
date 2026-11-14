from abc import ABC, abstractmethod


class GearBox(ABC):
    @abstractmethod
    def setGear(self):
        pass

class Engine:
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass


class Car(Engine,GearBox):
    def start(self):
        print("Starting")

    def stop(self):
        print("Stop")

    def setGear(self):
        print("Gearbox is ready")

    def drive(self):
        self.start()
        self.setGear()
        self.stop()



tesla = Car()
tesla.drive()











