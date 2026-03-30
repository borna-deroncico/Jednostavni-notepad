from abc import ABC, abstractmethod
from TextEditorModel import TextEditorModel
class Plugin(ABC):
    @abstractmethod
    def get_name(self):
        pass
    @abstractmethod
    def get_description(self):
        pass
    @abstractmethod
    def execute(self,model:TextEditorModel,undoManager,clipboardStack):
        pass