from abc import ABC, abstractmethod

class _RadioStation(ABC):
    def getURL(self):
        pass

    def getSongData(self):
        pass