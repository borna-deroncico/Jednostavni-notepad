from abc import ABC, abstractmethod
class EditAction(ABC):
    @abstractmethod
    def execute_do(self):
        pass
    @abstractmethod
    def execute_undo(self):
        pass

class UndoManager():
    pass