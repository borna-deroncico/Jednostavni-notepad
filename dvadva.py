import tkinter as tk

class TextEditorModel:
    def __init__(self,znakovniNiz):
        self.listaZnakova=znakovniNiz.split("\n")                
        self.cursorLocation = Location(0, 0)
        self.selectionRange = None

class Location:
    def __init__(self, line, column):
        self.line = line
        self.column = column

class LocationRange:
    def __init__(self, start, end):
        self.start = start  
        self.end = end
        
class TextEditor:
    def __init__(self,TextEditorModel):
        self.TextEditorModel=TextEditorModel


root = tk.Tk()
