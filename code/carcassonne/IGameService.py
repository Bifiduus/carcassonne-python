from abc import ABC, abstractmethod

class IGameService(ABC):
    @abstractmethod
    def placeTile(self):
        pass

    @abstractmethod
    def placeMeeple(self):
        pass
    
    @abstractmethod
    def getGameStates(self):
        pass
    
    @abstractmethod
    def playAI(self):
        pass