import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog, messagebox
from abc import ABC, abstractmethod
from Location import Location
from TextEditorModel import TextEditorModel
from LocationRange import LocationRange
from EditAction import EditAction
import os
from importlib import import_module
from Plugin import Plugin

def myfactory(moduleName):
    module = import_module(f"plugins.{moduleName}")  
    cls = getattr(module, moduleName)  
    return cls


class TextObserver(ABC):
    @abstractmethod
    def updateText(self):
        pass

class CursorObserver(ABC):
    @abstractmethod
    def updateCursorLocation(self, loc:Location):
        pass

class ClipboardObserver(ABC):
    @abstractmethod
    def updateClipboard(self):
        pass
class ClipboardStack:
    def __init__(self):
        self.texts = []
        self.clipboardObserver=[]
    def push(self, text):
        self.texts.append(text)
        self.notify_observers()
    def pop(self) -> str:
        if self.is_empty():
            return None
        pop=self.texts.pop()
        self.notify_observers()
        return pop
        
    def peek(self) -> str:
        if self.is_empty():
            return None
        return self.texts[-1]
    def is_empty(self) -> bool:
        return len(self.texts) == 0
    def delete(self):
        self.texts.clear()
        self.notify_observers()
    def addclipboardObserver(self,observer):
        if observer not in self.clipboardObserver:
            self.clipboardObserver.append(observer)
    def removeclipboardObserver(self,observer):
        if observer in self.clipboardObserver:
            self.clipboardObserver.remove(observer)
    def notify_observers(self):
        for observer in self.clipboardObserver:
            observer.updateClipboard()

class UndoObserver(ABC):
    @abstractmethod
    def update_undo_redo(self, undo_empty: bool, redo_empty: bool):
        pass

class UndoManager:
    def __init__(self):
        self.undoStack=[]
        self.redoStack=[]
        self.observes=[]
    def add_observer(self, observer: UndoObserver):
        if observer not in self.observes:
            self.observes.append(observer)

    def remove_observer(self, observer: UndoObserver):
        if observer in self.observes:
            self.observers.remove(observer)

    def notify_observers(self):
        undo_empty = len(self.undoStack) == 0
        redo_empty = len(self.redoStack) == 0
        for obs in self.observes:
            obs.update_undo_redo(undo_empty, redo_empty)
    
    def undo(self):
        naredba=self.undoStack.pop()
        self.redoStack.append(naredba)
        naredba.execute_undo()
        self.notify_observers()

    def push(self,c:EditAction):
        self.redoStack.clear()
        self.undoStack.append(c)
        self.notify_observers()


class TextEditor(tk.Canvas,CursorObserver,ClipboardObserver,UndoObserver):
    
    def __init__(self, parent, model, **kwargs):
        super().__init__(parent, **kwargs)
        #definiranje menua
        self.menuBar=tk.Menu(parent)
        self.model = model
        self.undoManager=UndoManager()
        self.undoManager.add_observer(self)
        self.clipboard=ClipboardStack()
        self.clipboard.addclipboardObserver(self)
        file_menu = tk.Menu(self.menuBar, tearoff=0)
        file_menu.add_command(label="Open", command=self.updateClipboard)
        file_menu.add_command(label="Save", command=self.updateClipboard)
        file_menu.add_command(label="Exit", command=self.updateClipboard)
        self.menuBar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(self.menuBar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undoFun)
        edit_menu.add_command(label="Redo", command=self.redoFun)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut)
        edit_menu.add_command(label="Copy", command=self.copy)
        edit_menu.add_command(label="Paste", command=self.paste)
        edit_menu.add_command(label="Paste and Take", command=self.updateClipboard)
        edit_menu.add_command(label="Delete selection", command=self.deleteSection)
        edit_menu.add_command(label="Clear document", command=self.clear)
        self.menuBar.add_cascade(label="Edit", menu=edit_menu)

        move_menu = tk.Menu(self.menuBar, tearoff=0)
        move_menu.add_command(label="Cursor to document start", command=lambda: setattr(self.model, "cursorLocation", Location(0, 0)))
        move_menu.add_command(label="Cursor to document end", command=self.end)
        self.menuBar.add_cascade(label="Move", menu=move_menu)

        plugin_menu=tk.Menu(self.menuBar,tearoff=0)
        plugins=[]
        for mymodule in os.listdir('plugins'):
            pass
            moduleName, moduleExt = os.path.splitext(mymodule)
            if moduleExt=='.py':
                plugin=myfactory(moduleName)()
                plugins.append(plugin)
        
        for plug in plugins:
            plugin_menu.add_command(label=plug.get_name(),command=lambda p=plug: self.plug_execute(p))
            pass
        self.menuBar.add_cascade(label="Plugins",menu=plugin_menu)

        parent.config(menu=self.menuBar)
        self.status_bar = tk.Label(parent, text="Ln 1, Col 1 | Lines: 1", anchor="w")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.model.addCursorObserver(self)
        self.font = tkFont.Font(family="Courier", size=14)
        self.line_height = 15
        self.char_width=self.font.measure("M")
        self.configure(bg="white")
        self.focus_set()
        self.bind("<Key>", self.on_key_press)
        self.cursor_visible=True
        self.began_selecting=False
        self.undo=True
        self.redo=True
        self.draw() 

    def plug_execute(self,plug:Plugin):
        plug.execute(self.model,self.undoManager,self.clipboard)

    def update_status_bar(self):
        row = self.model.cursorLocation.row + 1
        col = self.model.cursorLocation.column + 1
        total_lines = len(self.model.lines)
        self.status_bar.config(text=f"Ln {row}, Col {col} | Lines: {total_lines}")

    def deleteSection(self):
        selection = self.model.getSelectionRange()
        if selection.start != selection.end:
            editAction=self.model.deleteRange(selection)
            editAction.execute_do()
            self.undoManager.push(editAction)
            self.model.cursorLocation = selection.start
            self.model.setSelectionRange(LocationRange(selection.start, selection.start))
    def end(self):
        row=len(self.model.lines)-1
        column=len(self.model.lines[row])
        self.model.cursorLocation=Location(row,column)
    def clear(self):
        self.model.lines=[]

    def copy(self):
        sel_start = self.model.selectionRange.start
        sel_end = self.model.selectionRange.end
        if sel_start.column==sel_end.column and sel_start.row==sel_end.row:
            pass
        else:
            if (sel_start.row > sel_end.row) or (sel_start.row == sel_end.row and sel_start.column > sel_end.column):
                sel_start, sel_end = sel_end, sel_start

            row1, col1 = sel_start.row, sel_start.column
            row2, col2 = sel_end.row, sel_end.column
            if row1 == row2:
                line = self.model.lines[row1]
                self.clipboard.push(line[col1:col2])
            else:
                array=[]
                first_line = self.model.lines[row1][col1:]
                array.append(first_line)
                for i in range(row1+1, row2):
                    array.append(self.model.lines[i])
                array.append(self.model.lines[row2][:col2])
                self.clipboard.push('\n'.join(array))
    def cut(self):
        sel_start = self.model.selectionRange.start
        sel_end = self.model.selectionRange.end
        if sel_start.column==sel_end.column and sel_start.row==sel_end.row:
            pass
        else:
            if (sel_start.row > sel_end.row) or (sel_start.row == sel_end.row and sel_start.column > sel_end.column):
                sel_start, sel_end = sel_end, sel_start

            row1, col1 = sel_start.row, sel_start.column
            row2, col2 = sel_end.row, sel_end.column
            if row1 == row2:
                line = self.model.lines[row1]
                self.clipboard.push(line[col1:col2])
            else:
                array=[]
                first_line = self.model.lines[row1][col1:]
                array.append(first_line)
                for i in range(row1+1, row2):
                    array.append(self.model.lines[i])
                array.append(self.model.lines[row2][:col2])
                self.clipboard.push('\n'.join(array))

        editAction=self.model.deleteRange(self.model.selectionRange)
        editAction.execute_do()
        self.undoManager.push(editAction)
        self.model.setSelectionRange(LocationRange(Location(0,0), Location(0,0)))
    def paste(self):
        string=self.clipboard.pop()
        editAction=self.model.insert(string)
        editAction.execute_do()
        self.undoManager.push(editAction)
    def undoFun(self):
        if not self.undo:
                self.undoManager.undo()
    def redoFun(self):
        if not self.redo:
                editAction=self.undoManager.redoStack.pop()
                editAction.execute_do()
                self.undoManager.undoStack.append(editAction)

    def update_undo_redo(self, undo_empty: bool, redo_empty: bool):
        self.undo=undo_empty
        self.redo=redo_empty

    def updateClipboard(self):
        print("Clipboard changed")
    
    def updateCursorLocation(self, loc):
        self.model.cursorLocation.row = loc.row
        self.model.cursorLocation.column = loc.column
        self.update_status_bar()
        
    def on_key_press(self, event):
        cursor = self.model.cursorLocation

        if event.keysym == "Left":
            old_loc = Location(cursor.row, cursor.column)
            self.model.moveCursorLeft()
            new_loc = self.model.cursorLocation

            if event.state & 0x0001:
                if not self.began_selecting:
                    self.began_selecting = True
                    self.model.setSelectionRange(LocationRange(old_loc, new_loc))
                else:
                    current_range = self.model.getSelectionRange()
                    current_range.end = new_loc
                    self.model.setSelectionRange(current_range)
            else:
                self.began_selecting = False
                self.model.setSelectionRange(LocationRange(new_loc, new_loc))

        elif event.keysym == "Right":
            old_loc = Location(cursor.row, cursor.column)
            self.model.moveCursorRight()
            new_loc = self.model.cursorLocation

            if event.state & 0x0001:
                if not self.began_selecting:
                    self.began_selecting = True
                    self.model.setSelectionRange(LocationRange(old_loc, new_loc))
                else:
                    current_range = self.model.getSelectionRange()
                    current_range.end = new_loc
                    self.model.setSelectionRange(current_range)
            else:
                self.began_selecting = False
                self.model.setSelectionRange(LocationRange(new_loc, new_loc))

        elif event.keysym == "Up":
            old_loc = Location(cursor.row, cursor.column)
            self.model.moveCursorUp()
            new_loc = self.model.cursorLocation

            if event.state & 0x0001:
                if not self.began_selecting:
                    self.began_selecting = True
                    self.model.setSelectionRange(LocationRange(old_loc, new_loc))
                else:
                    current_range = self.model.getSelectionRange()
                    current_range.end = new_loc
                    self.model.setSelectionRange(current_range)
            else:
                self.began_selecting = False
                self.model.setSelectionRange(LocationRange(new_loc, new_loc))

        elif event.keysym == "Down":
            old_loc = Location(cursor.row, cursor.column)
            self.model.moveCursorDown()
            new_loc = self.model.cursorLocation

            if event.state & 0x0001:
                if not self.began_selecting:
                    self.began_selecting = True
                    self.model.setSelectionRange(LocationRange(old_loc, new_loc))
                else:
                    current_range = self.model.getSelectionRange()
                    current_range.end = new_loc
                    self.model.setSelectionRange(current_range)
            else:
                self.began_selecting = False
                self.model.setSelectionRange(LocationRange(new_loc, new_loc))
        elif event.keysym in ("BackSpace", "Delete"):
            selection = self.model.getSelectionRange()
            if selection.start != selection.end:
                editAction=self.model.deleteRange(selection)
                editAction.execute_do()
                self.undoManager.push(editAction)
                self.model.cursorLocation = selection.start
                self.model.setSelectionRange(LocationRange(selection.start, selection.start))
            elif event.keysym=="BackSpace":

                editAction=self.model.deleteBefore()
                editAction.execute_do()
                self.undoManager.push(editAction)
            elif event.keysym=="Delete":
                editAction=self.model.deleteAfter()
                editAction.execute_do()
                self.undoManager.push(editAction)

            self.began_selecting=False
        elif event.char.isalnum() or event.char==" ":
            editAction=self.model.insert(event.char)
            editAction.execute_do()
            self.undoManager.push(editAction)
        elif event.keysym=="Return":
            editAction=self.model.insert("\n")
            editAction.execute_do()
            self.undoManager.push(editAction)

        elif event.keysym.lower() == 'c' and (event.state & 0x0004):
            self.copy()

        elif event.keysym.lower() == 'x' and (event.state & 0x0004):    
            self.cut()

        elif event.keysym.lower() == 'v' and (event.state & 0x0004) and (event.state & 0x0001):
           self.paste()
        elif event.keysym.lower() == 'v' and (event.state & 0x0004):
            string=self.clipboard.peek()
            editAction=self.model.insert(string)
            editAction.execute_do()
            self.undoManager.push(editAction)
            pass
        elif event.keysym.lower()=='z' and (event.state & 0x0004):
            if not self.undo:
                self.undoManager.undo()
        elif event.keysym.lower()=='y' and (event.state & 0x0004):
            if not self.redo:
                print("uslo")
                editAction=self.undoManager.redoStack.pop()
                editAction.execute_do()
                self.undoManager.undoStack.append(editAction)
    
    def draw(self):
        self.delete("all")
        iter=self.model.allLines()

        sel_start = self.model.selectionRange.start
        sel_end = self.model.selectionRange.end
        if (sel_start.row > sel_end.row) or (sel_start.row == sel_end.row and sel_start.column > sel_end.column):
            sel_start, sel_end = sel_end, sel_start
        for i, ite in enumerate(iter):  
            text_id = self.create_text(5, i * self.line_height, anchor="nw", text=ite, font=self.font, fill="black")

            if sel_start.row <= i <= sel_end.row:
                if sel_start.row == sel_end.row:
                    x1 = sel_start.column * self.char_width + 5
                    x2 = sel_end.column * self.char_width + 5
                elif i == sel_start.row:
                    x1 = sel_start.column * self.char_width + 5
                    x2 = len(ite) * self.char_width + 5
                elif i == sel_end.row:
                    x1 = 5
                    x2 = sel_end.column * self.char_width + 5
                else:
                    x1 = 5
                    x2 = len(ite) * self.char_width + 5

                y1 = i * self.line_height
                y2 = y1 + self.line_height
                rect_id = self.create_rectangle(x1, y1, x2, y2, fill="blue", outline="")
                self.tag_raise(text_id, rect_id)
       
        if self.cursor_visible:
            row=self.model.cursorLocation.row * self.line_height + 2 
            col=self.model.cursorLocation.column * self.char_width + 5
            self.create_line(col, row, col, row + self.line_height, fill="black", width=1, tags="cursor")
        self.cursor_visible = not self.cursor_visible
        self.after(500, self.draw)

def main():
    root = tk.Tk()
    text = "Ovo je prvi red.\nOvo je drugi red.\nOvo je treci red."
    model = TextEditorModel(text)
    editor = TextEditor(root, model, width=800, height=600)
    editor.pack(fill="both", expand=True)
    root.mainloop()

main()