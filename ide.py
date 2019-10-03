#!/usr/bin/python3
# -- coding: utf-8 --
from __future__ import print_function

from PySide2.QtWidgets import (QPlainTextEdit, QWidget, QVBoxLayout, QApplication, QFileDialog, QMessageBox, QLabel, 
                                                    QHBoxLayout, QTextEdit, QToolBar, QComboBox, QAction, QLineEdit, QDialog, QPushButton, 
                                                     QToolButton, QMenu, QMainWindow, QInputDialog, QColorDialog, QStatusBar, QSystemTrayIcon)
from PySide2.QtGui import (QIcon, QPainter, QTextFormat, QColor, QTextCursor, QKeySequence, QClipboard, QTextDocument, 
                                        QPixmap, QStandardItemModel, QStandardItem, QCursor)
from PySide2.QtCore import (Qt, QRect, QDir, QFile, QFileInfo, QTextStream, QSettings, QTranslator, QLocale, 
                                            QProcess, QPoint, QSize, QCoreApplication, QStringListModel, QLibraryInfo)
from PySide2 import QtPrintSupport
from sys import argv
import inspect
from syntax import *
import os
import sys
import re

lineBarColor = QColor("#d3d7cf")
lineHighlightColor  = QColor("#393e46")
tab = chr(9)
eof = "\n"
iconsize = QSize(16, 16)

class NumberBar(QWidget):
    def __init__(self, parent = None):
        super(NumberBar, self).__init__(parent)
        self.editor = parent
        layout = QVBoxLayout()
        self.editor.blockCountChanged.connect(self.update_width)
        self.editor.updateRequest.connect(self.update_on_scroll)
        self.update_width('1')

    def update_on_scroll(self, rect, scroll):
        if self.isVisible():
            if scroll:
                self.scroll(0, scroll)
            else:
                self.update()

    def update_width(self, string):
        width = self.fontMetrics().horizontalAdvance(str(string)) + 8
        if self.width() != width:
            self.setFixedWidth(width)

    def paintEvent(self, event):
        if self.isVisible():
            block = self.editor.firstVisibleBlock()
            height = self.fontMetrics().height()
            number = block.blockNumber()
            painter = QPainter(self)
            painter.fillRect(event.rect(), lineBarColor)
            painter.drawRect(0, 0, event.rect().width() - 1, event.rect().height() - 1)
            font = painter.font()

            current_block = self.editor.textCursor().block().blockNumber() + 1

            condition = True
            while block.isValid() and condition:
                block_geometry = self.editor.blockBoundingGeometry(block)
                offset = self.editor.contentOffset()
                block_top = block_geometry.translated(offset).top()
                number += 1

                rect = QRect(0, block_top + 2, self.width() - 5, height)

                if number == current_block:
                    font.setBold(True)
                else:
                    font.setBold(False)

                painter.setFont(font)
                painter.drawText(rect, Qt.AlignRight, '%i'%number)

                if block_top > event.rect().bottom():
                    condition = False

                block = block.next()

            painter.end()

class myEditor(QMainWindow):
    def __init__(self, parent = None):
        super(myEditor, self).__init__(parent)

        self.root = QFileInfo.path(QFileInfo(QCoreApplication.arguments()[0]))
        self.wordList = []
        print("self.root is: ", self.root)
        self.appfolder = self.root
        self.statusBar().showMessage(self.appfolder)
        self.lineLabel = QLabel("line")
        self.statusBar().addPermanentWidget(self.lineLabel)
        self.settings = QSettings("IDE", "IDE")
        self.dirpath = QDir.homePath()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowIcon(QIcon.fromTheme("applications-python"))


        # Editor Widget ...
        self.editor = QPlainTextEdit()

        self.editor.setStyleSheet(stylesheet2(self))
        self.editor.cursorPositionChanged.connect(self.cursorPositionChanged)
        self.extra_selections = []
        self.mainText = "//Type program here\n"
        self.fname = ""
        self.filename = ""
        self.mypython = "2"
        # Line Numbers ...
        self.numbers = NumberBar(self.editor)
        # Syntax Highlighter ...
        self.highlighter = Highlighter(self.editor.document())
        # Laying out...
        layoutH = QHBoxLayout()
        layoutH.setSpacing(1.5)
        layoutH.addWidget(self.numbers)
        layoutH.addWidget(self.editor)
        ### statusbar
        self.statusBar()
        self.statusBar().setStyleSheet(stylesheet2(self))
        self.statusBar().showMessage('Welcome')
        ### begin toolbar
        tb = self.addToolBar("File")
        tb.setStyleSheet(stylesheet2(self))
        tb.setContextMenuPolicy(Qt.PreventContextMenu)
        tb.setIconSize(QSize(iconsize))
        tb.setMovable(True)
        tb.setAllowedAreas(Qt.AllToolBarAreas)
        tb.setFloatable(True)
       
        ### file buttons
        self.newAct = QAction("&New", self, shortcut=QKeySequence.New,
                statusTip="new file", triggered=self.newFile)
        self.newAct.setIcon(QIcon.fromTheme(self.root + "/icons/new24"))
        
        self.openAct = QAction("&Open", self, shortcut=QKeySequence.Open,
                statusTip="open file", triggered=self.openFile)
        self.openAct.setIcon(QIcon.fromTheme(self.root + "/icons/open24"))

        self.saveAct = QAction("&Save", self, shortcut=QKeySequence.Save,
                statusTip="save file", triggered=self.fileSave)
        self.saveAct.setIcon(QIcon.fromTheme(self.root + "/icons/floppy24"))
        
        self.saveAsAct = QAction("&Save as ...", self, shortcut=QKeySequence.SaveAs,
                statusTip="save file as ...", triggered=self.fileSaveAs)
        self.saveAsAct.setIcon(QIcon.fromTheme(self.root + "/icons/floppy25"))
        
        ### comment buttons       
        # tb.addSeparator()           
        self.commentAct = QAction("Comment Line", self, shortcut="F2",
                statusTip="Comment Line (F2)", triggered=self.commentLine)
        self.commentAct.setIcon(QIcon.fromTheme(self.root + "/icons/comment"))
        tb.addAction(self.commentAct)
                         
        self.uncommentAct = QAction("Uncomment Line", self, shortcut="F3",
                statusTip="Uncomment Line (F3)", triggered=self.uncommentLine)
        self.uncommentAct.setIcon(QIcon.fromTheme(self.root + "/icons/uncomment"))
        tb.addAction(self.uncommentAct)  
        
        self.commentBlockAct = QAction("Comment Block", self, shortcut="F6",
                statusTip="Comment selected block (F6)", triggered=self.commentBlock)
        self.commentBlockAct.setIcon(QIcon.fromTheme(self.root + "/icons/commentBlock"))
        tb.addAction(self.commentBlockAct)  
        
        self.uncommentBlockAct = QAction("Uncomment Block", self, shortcut="F7",
                statusTip="Uncomment selected block (F7)", triggered=self.uncommentBlock)
        self.uncommentBlockAct.setIcon(QIcon.fromTheme(self.root + "/icons/uncommentBlock"))
        tb.addAction(self.uncommentBlockAct)

        ### print preview
        self.printPreviewAct = QAction("Print Preview", self, shortcut="Ctrl+Shift+P",
                statusTip="Preview Document", triggered=self.handlePrintPreview)
        self.printPreviewAct.setIcon(QIcon.fromTheme("document-print-preview"))
        tb.addAction(self.printPreviewAct)
        ### print
        self.printAct = QAction("Print", self, shortcut=QKeySequence.Print,
                statusTip="Print Document", triggered=self.handlePrint)
        self.printAct.setIcon(QIcon.fromTheme("document-print"))
        tb.addAction(self.printAct) 

        ### find / replace toolbar
        self.addToolBarBreak()
        tbf = self.addToolBar("Find")
        tbf.setStyleSheet(stylesheet2(self))
        tbf.setContextMenuPolicy(Qt.PreventContextMenu)
        tbf.setIconSize(QSize(iconsize))
        self.findfield = QLineEdit()
        self.findfield.setStyleSheet(stylesheet2(self))
        self.findfield.addAction(QIcon.fromTheme("edit-find"), QLineEdit.LeadingPosition)
        self.findfield.setClearButtonEnabled(True)
        self.findfield.setFixedWidth(150)
        self.findfield.setPlaceholderText("find")
        self.findfield.setToolTip("press RETURN to find")
        self.findfield.setText("")
        ft = self.findfield.text()
        self.findfield.returnPressed.connect(self.findText)
        tbf.addWidget(self.findfield)
        self.replacefield = QLineEdit()
        self.replacefield.setStyleSheet(stylesheet2(self))
        self.replacefield.addAction(QIcon.fromTheme("edit-find-and-replace"), QLineEdit.LeadingPosition)
        self.replacefield.setClearButtonEnabled(True)
        self.replacefield.setFixedWidth(150)
        self.replacefield.setPlaceholderText("replace with")
        self.replacefield.setToolTip("press RETURN to replace the first")
        self.replacefield.returnPressed.connect(self.replaceOne)
        tbf.addSeparator() 
        tbf.addWidget(self.replacefield)
        tbf.addSeparator()
        
        self.repAllAct = QPushButton("replace all") 
        self.repAllAct.setFixedWidth(100)
        self.repAllAct.setStyleSheet(stylesheet2(self))
        self.repAllAct.setIcon(QIcon.fromTheme("gtk-find-and-replace"))
        self.repAllAct.setStatusTip("replace all")
        self.repAllAct.clicked.connect(self.replaceAll)
        tbf.addWidget(self.repAllAct)
        tbf.addSeparator()
        self.gotofield = QLineEdit()
        self.gotofield.setStyleSheet(stylesheet2(self))
        self.gotofield.addAction(QIcon.fromTheme("next"), QLineEdit.LeadingPosition)
        self.gotofield.setClearButtonEnabled(True)
        self.gotofield.setFixedWidth(120)
        self.gotofield.setPlaceholderText("Go to line")
        self.gotofield.setToolTip("press RETURN to go to line")
        self.gotofield.returnPressed.connect(self.gotoLine)
        tbf.addWidget(self.gotofield)
        
        tbf.addAction(QAction(QIcon.fromTheme("document-properties"), "check && reindent Text", self, triggered=self.reindentText))
        
        layoutV = QVBoxLayout()
        
        bar=self.menuBar()
        bar.setStyleSheet(stylesheet2(self))
        self.filemenu=bar.addMenu("File")
        self.filemenu.setStyleSheet(stylesheet2(self))
        self.separatorAct = self.filemenu.addSeparator()
        self.filemenu.addAction(self.newAct)
        self.filemenu.addAction(self.openAct)
        self.filemenu.addAction(self.saveAct)
        self.filemenu.addAction(self.saveAsAct)
        self.filemenu.addSeparator()
        
        editmenu = bar.addMenu("Edit")
        editmenu.setStyleSheet(stylesheet2(self))
        editmenu.addAction(QAction(QIcon.fromTheme('edit-undo'), "Undo", self, triggered = self.editor.undo, shortcut = "Ctrl+U"))
        editmenu.addAction(QAction(QIcon.fromTheme('edit-redo'), "Redo", self, triggered = self.editor.redo, shortcut = "Shift+Ctrl+u"))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon.fromTheme('edit-copy'), "Copy", self, triggered = self.editor.copy, shortcut = "Ctrl+C"))
        editmenu.addAction(QAction(QIcon.fromTheme('edit-cut'), "Cut", self, triggered = self.editor.cut, shortcut = "Ctrl+X"))
        editmenu.addAction(QAction(QIcon.fromTheme('edit-paste'), "Paste", self, triggered = self.editor.paste, shortcut = "Ctrl+V"))
        editmenu.addAction(QAction(QIcon.fromTheme('edit-delete'), "Delete", self, triggered = self.editor.cut, shortcut = "Del"))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon.fromTheme('edit-select-all'), "Select All", self, triggered = self.editor.selectAll, shortcut = "Ctrl+a"))
        editmenu.addSeparator()

        layoutV.addLayout(layoutH)
        ### main window
        mq = QWidget(self)
        mq.setLayout(layoutV)
        self.setCentralWidget(mq)
        
        # Event Filter ...
#        self.installEventFilter(self)
        self.editor.setFocus()
        self.cursor = QTextCursor()
        self.editor.setTextCursor(self.cursor)
        self.editor.setPlainText(self.mainText)
        self.editor.moveCursor(self.cursor.End)
        self.editor.document().modificationChanged.connect(self.setWindowModified)
        
        # Brackets ExtraSelection ...
        self.left_selected_bracket  = QTextEdit.ExtraSelection()
        self.right_selected_bracket = QTextEdit.ExtraSelection()

    def keyPressEvent(self, event):
        if  self.editor.hasFocus():
            if event.key() == Qt.Key_F10:
                self.findNextWord()

    def cursorPositionChanged(self):
        line = self.editor.textCursor().blockNumber() + 1
        pos = self.editor.textCursor().positionInBlock()
        self.lineLabel.setText("Line " + str(line) + " , Position " + str(pos))
        
    def reindentText(self):
        if self.editor.toPlainText() == "" or self.editor.toPlainText() == self.mainText:
            self.statusBar().showMessage("No code to reindent.")
        else:
            self.editor.selectAll()
            tab = "\t"
            oldtext = self.editor.textCursor().selectedText()
            newtext = oldtext.replace(tab, "    ")
            self.editor.textCursor().insertText(newtext)    
            self.statusBar().showMessage("Reindented.")

    def findNextWord(self):
        if self.editor.textCursor().selectedText() == "":
            self.editor.moveCursor(QTextCursor.StartOfWord, QTextCursor.MoveAnchor)
            self.editor.moveCursor(QTextCursor.EndOfWord, QTextCursor.KeepAnchor)
        rtext = self.editor.textCursor().selectedText()
        self.findfield.setText(rtext)
        self.findText()
        
    def dataReady(self):
        out = ""
        try:
            out = str(self.process.readAll(), encoding = 'utf8').rstrip()
        except TypeError:
            self.msgbox("Error", str(self.process.readAll(), encoding = 'utf8'))
            out = str(self.process.readAll()).rstrip()
        self.mylabel.moveCursor(self.cursor.Start)
        self.mylabel.append(out)    
        if self.mylabel.find("line", QTextDocument.FindWholeWords):
            t = self.mylabel.toPlainText().partition("line")[2].partition("\n")[0].lstrip()
            if t.find(",", 0):
                tr = t.partition(",")[0]
            else:
                tr = t.lstrip()
            self.gotoErrorLine(tr)
        else:
            return
        self.mylabel.moveCursor(self.cursor.End)
        self.mylabel.ensureCursorVisible()
        
    def getLineNumber(self):
        self.editor.moveCursor(self.cursor.StartOfLine)
        linenumber = self.editor.textCursor().blockNumber() + 1
        return linenumber
            
    def gotoLine(self):
        ln = int(self.gotofield.text())
        linecursor = QTextCursor(self.editor.document().findBlockByLineNumber(ln-1))
        self.editor.moveCursor(QTextCursor.End)
        self.editor.setTextCursor(linecursor)
        
    def gotoErrorLine(self, ln):
        if ln.isalnum:
            t = int(ln)
            if t != 0:
                linecursor = QTextCursor(self.editor.document().findBlockByLineNumber(t-1))
                self.editor.moveCursor(QTextCursor.End)
                self.editor.setTextCursor(linecursor)
                self.editor.moveCursor(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            else:
                return
                
    def clearLabel(self):
        self.mylabel.setText("")
            
        ### New File
    def newFile(self):
        if self.maybeSave():
            self.editor.clear()
            self.editor.setPlainText(self.mainText)
            self.filename = ""
            self.setModified(False)
            self.editor.moveCursor(self.cursor.End)
            self.statusBar().showMessage("new File created.")
            self.editor.setFocus()
            self.setWindowTitle("new File[*]")
            
       ### open File
    def openFileOnStart(self, path=None):
        if path:
            inFile = QFile(path)
            if inFile.open(QFile.ReadWrite | QFile.Text):
                text = inFile.readAll()
                try:
                        # Python v3.
                    text = str(text, encoding = 'utf8')
                except TypeError:
                        # Python v2.
                    text = str(text)
                self.editor.setPlainText(text.replace(tab, "    "))
                self.setModified(False)
                self.setCurrentFile(path)
                self.editor.setFocus()
    ### open File
    def openFile(self, path=None):
        if self.maybeSave():
            if not path:
                path, _ = QFileDialog.getOpenFileName(self, "Open File", self.dirpath,
                    "Python Files (*.py);; all Files (*)")

            if path:
                self.openFileOnStart(path)
            
    def fileSave(self):
        if (self.filename != ""):
            file = QFile(self.filename)
            if not file.open( QFile.WriteOnly | QFile.Text):
                QMessageBox.warning(self, "Error",
                        "Cannot write file %s:\n%s." % (self.filename, file.errorString()))
                return

            outstr = QTextStream(file)
            QApplication.setOverrideCursor(Qt.WaitCursor)
            outstr << self.editor.toPlainText()
            QApplication.restoreOverrideCursor()                
            self.setModified(False)
            self.fname = QFileInfo(self.filename).fileName() 
            self.setWindowTitle(self.fname + "[*]")
            self.statusBar().showMessage("File saved.")
            self.setCurrentFile(self.filename)
            self.editor.setFocus()
            
            
        else:
            self.fileSaveAs()
            
            ### save File
    def fileSaveAs(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save as...", self.filename,
                "Python files (*.py)")

        if not fn:
            print("Error saving")
            return False

        lfn = fn.lower()
        if not lfn.endswith('.py'):
            fn += '.py'

        self.filename = fn
        self.fname = QFileInfo(QFile(fn).fileName())
        return self.fileSave()
        
    def closeEvent(self, e):
        self.writeSettings()
        if self.maybeSave():
            e.accept()
        else:
            e.ignore()
        
        ### ask to save
    def maybeSave(self):
        if not self.isModified():
            return True

        if self.filename.startswith(':/'):
            return True

        ret = QMessageBox.question(self, "Message",
                "<h4><p>The document was modified.</p>\n" \
                "<p>Do you want to save changes?</p></h4>",
                QMessageBox.Yes | QMessageBox.Discard | QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            if self.filename == "":
                self.fileSaveAs()
                return False
            else:
                self.fileSave()
                return True

        if ret == QMessageBox.Cancel:
            return False

        return True   
            
    def readData(self, cmd):
        self.mylabel.clear()
        dname = QFileInfo(self.filename).filePath().replace(QFileInfo(self.filename).fileName(), "")
        self.statusBar().showMessage(str(dname))
        QProcess().execute("cd '" + dname + "'")
        self.process.start(cmd,['-u', dname + self.strippedName(self.filename)])
        
    def commentBlock(self):
        self.editor.copy()
        clipboard = QApplication.clipboard();
        originalText = clipboard.text()
        mt1 = "/*\n"
        mt2 = "\n*/"
        mt = mt1 + originalText + mt2
        clipboard.setText(mt)
        self.editor.paste()
        
    def uncommentBlock(self):
        self.editor.copy()
        clipboard = QApplication.clipboard();
        originalText = clipboard.text()
        mt1 = "/*\n"
        mt2 = "\n*/"
        clipboard.setText(originalText.replace(mt1, "").replace(mt2, ""))
        self.editor.paste()
        
        self.statusBar().showMessage("Added block comment")
            
    def commentLine(self):
        newline = u"\u2029"
        comment = "//"
        list = []
        ot = self.editor.textCursor().selectedText()
        if not self.editor.textCursor().selectedText() == "":
            ### multiple lines selected        
            theList  = ot.splitlines()
            linecount = ot.count(newline)
            for i in range(linecount + 1):
                list.insert(i, comment + theList[i])
            self.editor.textCursor().insertText(newline.join(list))
            self.setModified(True)    
            self.statusBar().showMessage("added comment")
        else:
            ### one line selected
            self.editor.moveCursor(QTextCursor.StartOfLine)
            self.editor.textCursor().insertText("//")
            
            
    def uncommentLine(self):
        comment = "//"
        newline = u"\u2029"
        list = []
        ot = self.editor.textCursor().selectedText()
        if not self.editor.textCursor().selectedText() == "":
        ### multiple lines selected 
            theList  = ot.splitlines()
            linecount = ot.count(newline)
            for i in range(linecount + 1):
                list.insert(i, (theList[i]).replace(comment, "", 1))
            self.editor.textCursor().insertText(newline.join(list))
            self.setModified(True)    
            self.statusBar().showMessage("comment removed")
        else:
            ### one line selected
            self.editor.moveCursor(QTextCursor.StartOfLine)
            self.editor.moveCursor(QTextCursor.Right, QTextCursor.KeepAnchor)
            if self.editor.textCursor().selectedText() == comment:
                self.editor.textCursor().deleteChar()
                self.editor.moveCursor(QTextCursor.StartOfLine)
            else:
                self.editor.moveCursor(QTextCursor.StartOfLine)
        
    def goToLine(self, ft):
        self.editor.moveCursor(int(self.gofield.currentText()),QTextCursor.MoveAnchor)
        
    def findText(self):
        word = self.findfield.text()
        if self.editor.find(word):
            linenumber = self.editor.textCursor().blockNumber() + 1
            self.statusBar().showMessage("found <b>'" + self.findfield.text() + "'</b> at Line: " + str(linenumber))
            self.editor.centerCursor()
        else:
            self.statusBar().showMessage("<b>'" + self.findfield.text() + "'</b> not found")
            self.editor.moveCursor(QTextCursor.Start)            
            if self.editor.find(word):
                linenumber = self.editor.textCursor().blockNumber() + 1
                self.statusBar().showMessage("found <b>'" + self.findfield.text() + "'</b> at Line: " + str(linenumber))
                self.editor.centerCursor()
            
    def handleQuit(self):
        if self.maybeSave():
            print("Goodbye ...")
            app.quit()

    def set_numbers_visible(self, value = True):
        self.numbers.setVisible(False)

    def paintEvent(self, event):
        highlighted_line = QTextEdit.ExtraSelection()
        highlighted_line.format.setBackground(lineHighlightColor)
        highlighted_line.format.setProperty(QTextFormat
                                                 .FullWidthSelection,
                                                  True)                                     
        highlighted_line.cursor = self.editor.textCursor()
        highlighted_line.cursor.clearSelection()
        self.editor.setExtraSelections([highlighted_line,
                                      self.left_selected_bracket,
                                      self.right_selected_bracket])

    def document(self):
        return self.editor.document
        
    def isModified(self):
        return self.editor.document().isModified()

    def setModified(self, modified):
        self.editor.document().setModified(modified)

    def setLineWrapMode(self, mode):
        self.editor.setLineWrapMode(mode)

    def clear(self):
        self.editor.clear()

    def setPlainText(self, *args, **kwargs):
        self.editor.setPlainText(*args, **kwargs)

    def setDocumentTitle(self, *args, **kwargs):
        self.editor.setDocumentTitle(*args, **kwargs)

    def set_number_bar_visible(self, value):
        self.numbers.setVisible(value)
        
    def replaceAll(self):
        if not self.editor.document().toPlainText() == "":
            if not self.findfield.text() == "":
                self.statusBar().showMessage("Replacing all")
                oldtext = self.editor.document().toPlainText()
                newtext = oldtext.replace(self.findfield.text(), self.replacefield.text())
                self.editor.setPlainText(newtext)
                self.setModified(True)
            else:
                self.statusBar().showMessage("nothing to replace")
        else:
                self.statusBar().showMessage("no text")
        
    def replaceOne(self):
        if not self.editor.document().toPlainText() == "":
            if not self.findfield.text() == "":
                self.statusBar().showMessage("Replacing all")
                oldtext = self.editor.document().toPlainText()
                newtext = oldtext.replace(self.findfield.text(), self.replacefield.text(), 1)
                self.editor.setPlainText(newtext)
                self.setModified(True)
            else:
                self.statusBar().showMessage("nothing to replace")
        else:
                self.statusBar().showMessage("no text")
        
    def setCurrentFile(self, fileName):
        self.filename = fileName
        if self.filename:
            self.setWindowTitle(self.strippedName(self.filename) + "[*]")
        else:
            self.setWindowTitle("no File")      
        
    def strippedName(self, fullFileName):
        return QFileInfo(fullFileName).fileName()

    def readSettings(self):
        if self.settings.value("pos") != "":
            pos = self.settings.value("pos", QPoint(200, 200))
            self.move(pos)
        if self.settings.value("size") != "":
            size = self.settings.value("size", QSize(400, 400))
            self.resize(size)

    def writeSettings(self):
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("size", self.size())
        
    def msgbox(self,title, message):
        QMessageBox.warning(self, title, message)
        
    def handlePrint(self):
        if self.editor.toPlainText() == "":
            self.statusBar().showMessage("no text")
        else:
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec_() == QDialog.Accepted:
                self.handlePaintRequest(dialog.printer())
                self.statusBar().showMessage("Document printed")
            
    def handlePrintPreview(self):
        if self.editor.toPlainText() == "":
            self.statusBar().showMessage("no text")
        else:
            dialog = QtPrintSupport.QPrintPreviewDialog()
            dialog.setFixedSize(900,650)
            dialog.paintRequested.connect(self.handlePaintRequest)
            dialog.exec_()
            self.statusBar().showMessage("Print Preview closed")

    def handlePaintRequest(self, printer):
        printer.setDocName(self.filename)
        document = self.editor.document()
        document.print_(printer)


def stylesheet2(self):
    return """
    QPlainTextEdit
    {
        font-family: Helvetica;
        font-size: 13px;
        background: #2b2b2b;
        color: #ccc;
        border: 1px solid #1EAE3D;
    }
    QTextEdit
    {
        background: #292929;
        color: #1EAE3D;
        font-family: Monospace;
        font-size: 8pt;
        padding-left: 6px;
        border: 1px solid #1EAE3D;
    }
    QStatusBar
    {
        font-family: Helvetica;
        color: #204a87;
        font-size: 8pt;
    }
    QLabel
    {
        font-family: Helvetica;
        color: #204a87;
        font-size: 8pt;
    }
    QLineEdit
    {
        font-family: Helvetica;
        font-size: 8pt;
    }
    QPushButton
    {
        font-family: Helvetica;
        font-size: 8pt;
    }
    QComboBox
    {
        font-family: Helvetica;
        font-size: 8pt;
    }
    QMenuBar
    {
        font-family: Helvetica;
        font-size: 8pt;
    }
    QMenu
    {
        font-family: Helvetica;
        font-size: 8pt;
    }
    QToolBar
    {
        background: transparent;
    }
    """       

if __name__ == '__main__':
    app = QApplication(argv)
    translator = QTranslator(app)
    locale = QLocale.system().name()
    print(locale)
    path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    print(path)
    translator.load('qt_%s' % locale, path)
    app.installTranslator(translator)
    win = myEditor()
    win.setWindowTitle("IDE" + "[*]")
    win.show()
    if len(argv) > 1:
        print(argv[1])
        win.openFileOnStart(argv[1])

    sys.exit(app.exec_())