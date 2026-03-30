from Location import Location
from LocationRange import LocationRange
from EditAction import EditAction
class TextEditorModel:
    def __init__(self, text):
        self.lines = text.split('\n')
        self.cursorLocation = Location(0, 0)
        self.selectionRange = LocationRange(Location(0,0),Location(0,0))
        self.cursorObservers=[]
        self.TextObservers=[]
    def addTextObserver(self,observer):
        if observer not in self.TextObservers:
            self.TextObservers.append(observer)
    def removeTextObserver(self,observer):
        if observer in self.TextObservers:
            self.TextObservers.remove(observer)
    
    def notifyTextObservers(self):
        for observer in self.TextObservers:
            observer.updateText(self.TextObservers)

    def addCursorObserver(self, observer):
        if observer not in self.cursorObservers:
            self.cursorObservers.append(observer)

    def removeCursorObserver(self, observer):
        if observer in self.cursorObservers:
            self.cursorObservers.remove(observer)

    def notifyCursorObservers(self):
        for observer in self.cursorObservers:
            observer.updateCursorLocation(self.cursorLocation)
    
    def deleteBefore(self):
        #if self.cursorLocation.column > 0:
        #    indexline = self.cursorLocation.row
        #    indextext = self.cursorLocation.column - 1
        #    line = self.lines[indexline]
        #    new_line = line[:indextext] + line[indextext + 1:]
        #    self.lines[indexline] = new_line  
        #    self.cursorLocation.column -= 1
        #    self.notifyTextObservers()
        class _DeleteBeforeAction(EditAction):
            def __init__(inner_self):
                inner_self.original_cursor = Location(self.cursorLocation.row, self.cursorLocation.column)
                inner_self.original_lines = []
                for i,line in enumerate(self.lines):
                    inner_self.original_lines.append(line)

            def execute_do(inner_self):
                if self.cursorLocation.column > 0:
                    indexline = self.cursorLocation.row
                    indextext = self.cursorLocation.column - 1
                    line = self.lines[indexline]
                    new_line = line[:indextext] + line[indextext + 1:]
                    self.lines[indexline] = new_line  
                    self.cursorLocation.column -= 1
                    self.notifyTextObservers()
            def execute_undo(inner_self):
                self.cursorLocation = Location(inner_self.original_cursor.row, inner_self.original_cursor.column)
                self.lines=inner_self.original_lines
                for i,line in enumerate(inner_self.original_lines):
                    self.lines[i]=line
                self.notifyTextObservers()
        return _DeleteBeforeAction()


    def deleteAfter(self):
        #if len(self.lines[self.cursorLocation.row])>self.cursorLocation.column:
        #    indexline=self.cursorLocation.row
        #    indextext=self.cursorLocation.column
        #    line=self.lines[indexline]
        #    new_line = line[:indextext] + line[indextext + 1:]
        #    self.lines[indexline]=new_line
        #    self.notifyTextObservers() 
        class _DeleteAfterAction(EditAction):
            def __init__(inner_self):
                inner_self.original_cursor = Location(self.cursorLocation.row, self.cursorLocation.column)
                inner_self.original_lines = []
                for i,line in enumerate(self.lines):
                    inner_self.original_lines.append(line)
            def execute_do(inner_self):
                if len(self.lines[self.cursorLocation.row])>self.cursorLocation.column:
                    indexline=self.cursorLocation.row
                    indextext=self.cursorLocation.column
                    line=self.lines[indexline]
                    new_line = line[:indextext] + line[indextext + 1:]
                    self.lines[indexline]=new_line
                    self.notifyTextObservers() 
            def execute_undo(inner_self):
                self.cursorLocation = Location(inner_self.original_cursor.row, inner_self.original_cursor.column)
                self.lines=inner_self.original_lines
                for i,line in enumerate(inner_self.original_lines):
                    self.lines[i]=line
                self.notifyTextObservers()
        return _DeleteAfterAction()
        


    def deleteRange(self, range: LocationRange):
        #start = range.start
        #end = range.end
        #if (start.row > end.row) or (start.row == end.row and start.column > end.column):
        #    start, end = end, start  
        #row1, col1 = start.row, start.column
        #row2, col2 = end.row, end.column

        #if row1 == row2:
        #    line = self.lines[row1]
        #    self.lines[row1] = line[:col1] + line[col2:]
        #else:
        #    first_line = self.lines[row1][:col1]
        #    last_line = self.lines[row2][col2:]
        #    self.lines[row1] = first_line + last_line
        #    del self.lines[row1 + 1: row2 + 1]
        #self.notifyTextObservers()
        class _deleteRangeAction(EditAction):
            def __init__(inner_self):
                inner_self.original_cursor = Location(self.cursorLocation.row, self.cursorLocation.column)
                inner_self.original_lines = []
                for i,line in enumerate(self.lines):
                    inner_self.original_lines.append(line)
            def execute_do(inner_self):
                start = range.start
                end = range.end
                if (start.row > end.row) or (start.row == end.row and start.column > end.column):
                    start, end = end, start  
                row1, col1 = start.row, start.column
                row2, col2 = end.row, end.column

                if row1 == row2:
                    line = self.lines[row1]
                    self.lines[row1] = line[:col1] + line[col2:]
                else:
                    first_line = self.lines[row1][:col1]
                    last_line = self.lines[row2][col2:]
                    self.lines[row1] = first_line + last_line
                    del self.lines[row1 + 1: row2 + 1]
                self.notifyTextObservers()
            def execute_undo(inner_self):
                self.cursorLocation = Location(inner_self.original_cursor.row, inner_self.original_cursor.column)
                self.lines=inner_self.original_lines
                for i,line in enumerate(inner_self.original_lines):
                    self.lines[i]=line
                self.notifyTextObservers()
                
        return _deleteRangeAction()



    def getSelectionRange(self):
        return self.selectionRange
    
    def setSelectionRange(self,range:LocationRange):
        self.selectionRange.start=range.start
        self.selectionRange.end=range.end
        self.notifyTextObservers()
    
    def moveCursorLeft(self):
        self.cursorLocation.column=max(0,self.cursorLocation.column-1)
        self.notifyCursorObservers()

    def moveCursorRight(self):
        if len(self.lines[self.cursorLocation.row])>self.cursorLocation.column:
            self.cursorLocation.column=max(0,self.cursorLocation.column+1)
            self.notifyCursorObservers()

    def moveCursorUp(self):
        self.cursorLocation.row= max(0,self.cursorLocation.row-1)
        self.notifyCursorObservers()

    def moveCursorDown(self):
        if len(self.lines)-1>self.cursorLocation.row:
            self.cursorLocation.row= max(0,self.cursorLocation.row+1)
            self.notifyCursorObservers()

    def allLines(self):
        return iter(self.lines)
    
    def linesRange(self,index1,index2):
        return iter(self.lines[index1-1:index2-1])
    
    def insert(self,c):
        class _insertAction(EditAction):
            def __init__(inner_self):
                inner_self.text = c
                inner_self.original_cursor = Location(self.cursorLocation.row, self.cursorLocation.column)
                inner_self.affected_range = None
                inner_self.original_lines = []
                for i,line in enumerate(self.lines):
                    inner_self.original_lines.append(line)

            def execute_do(inner_self):
                if c=="\n":
                    old_lines_before=self.lines[self.cursorLocation.row][:self.cursorLocation.column]
                    old_lines_after=self.lines[self.cursorLocation.row][self.cursorLocation.column:]
                    self.lines[self.cursorLocation.row] = old_lines_before
                    self.lines.insert(self.cursorLocation.row+1,old_lines_after)
                    self.cursorLocation.column=0
                    self.cursorLocation.row=self.cursorLocation.row+1
                elif "\n" in c:
                    arry=c.split("\n")
                    old_lines_before=self.lines[self.cursorLocation.row][:self.cursorLocation.column]
                    old_lines_after=self.lines[self.cursorLocation.row][self.cursorLocation.column:]
                    first_line=arry[0]
                    self.lines[self.cursorLocation.row]=old_lines_before + first_line
                    i=self.cursorLocation.row +1
                    for line in arry[1:]:
                        self.lines.insert(i,line)
                        i=i+1
                    self.lines.insert(i,old_lines_after)
                    self.cursorLocation.column=0
                    self.cursorLocation.row=self.cursorLocation.row+len(arry)
                    
                else:
                    old_lines_before=self.lines[self.cursorLocation.row][:self.cursorLocation.column]
                    old_lines_after=self.lines[self.cursorLocation.row][self.cursorLocation.column:]
                    self.lines[self.cursorLocation.row] = old_lines_before+c+old_lines_after
                    self.cursorLocation.column=self.cursorLocation.column+1
            def execute_undo(inner_self):
                self.cursorLocation = Location(inner_self.original_cursor.row, inner_self.original_cursor.column)
                self.lines=inner_self.original_lines
                for i,line in enumerate(inner_self.original_lines):
                    self.lines[i]=line
                self.notifyTextObservers()
        return _insertAction()
        

