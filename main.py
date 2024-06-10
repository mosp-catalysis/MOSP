# -*- coding: utf-8 -*-
"""
@author: yinglei
"""

import wx
import os
import sys  
import win32api
from views.input_panel import InputPanel
from views.visual_panel import glPanel, pltPanel

APP_TITLE = '  MOSP  '
APP_ICON = 'assets/logo.ico'
BG_COLOR = 'white'

class LogPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        Box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(Box)
        nm1 = wx.StaticBox(self, -1, 'Log')
        nmSizer1 = wx.StaticBoxSizer(nm1, wx.VERTICAL)
        
        self.multiText = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE|wx.TE_READONLY) 
        self.multiText.SetInsertionPoint(0)
        nmSizer1.Add(self.multiText, 1, wx.EXPAND | wx.ALL, 10)
        
        Box.Add(nmSizer1, 1, wx.EXPAND | wx.ALL, 10)

    def Write(self, txt):
        self.multiText.write(txt)

    def WriteTexts(self, txts):
        for txt in txts:
            self.multiText.write('  %s' % txt)

    def WriteText(self, txt):
        self.multiText.write('%s\n' % txt)


class mainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title=APP_TITLE)
        self.initUI()

        splitterMain = wx.SplitterWindow(self, -1)
        splitter = wx.SplitterWindow(splitterMain, -1)
        logPanel = LogPanel(splitter)

        self.VisualPanel = wx.Notebook(splitter, style=wx.BK_DEFAULT)
        self.glPanel = glPanel(self.VisualPanel, logPanel)
        self.pltPanle = pltPanel(self.VisualPanel, logPanel)
        self.pltPanle.SetScrollRate(10, 10)
        self.VisualPanel.AddPage(self.glPanel, 'Model Visual')
        self.VisualPanel.AddPage(self.pltPanle, 'Data Visual')

        self.InputPanel = InputPanel(splitterMain, self, logPanel)
        self.InputPanel.SetScrollRate(10, 10)
        self.InputPanel.SetFocus()

        splitterMain.SplitVertically(self.InputPanel, splitter) 
        splitterMain.SetSashGravity(0.618)
        splitter.SplitHorizontally(self.VisualPanel, logPanel)
        splitter.SetSashGravity(0.75)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(8)
        sizer.Add(splitterMain, 1, flag=wx.EXPAND)
        self.SetSizer(sizer)
        sizer.AddSpacer(8)

        self.createMenuBar() 
        self.Bind(wx.EVT_CLOSE, self.OnDestroy)

    def initUI(self):
        if hasattr(sys, "frozen") and getattr(sys, "frozen") == "windows_exe":
            exeName = win32api.GetModuleFileName(win32api.GetModuleHandle(None))
            icon = wx.Icon(exeName, wx.BITMAP_TYPE_ICO)
        else :
            icon = wx.Icon(APP_ICON, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        font = wx.Font(12,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_NORMAL,
                       False, 'Calibri')
        self.SetFont(font)
        self.SetBackgroundColour(BG_COLOR)
        self.Center()
        self.Maximize(True)

    def menuData(self):
        return (("&File",
                    ("&Save", "Save Input files", self.OnSave),
                    ("&Load", "Load Input files", self.OnLoad),
                    #("&Clear", "Clear Inputs", self.OnClear),
                    ("", "", ""),
                    ("&Quit", "Quit", self.OnCloseWindow)),
                ("&Run",
                    ("&Run MSR", "Run MSR Simulations", self.runMSR),
                    ("&Run KMC", "Run KMC Simulations", self.runKMC)))

    def createMenuBar(self):
        menuBar = wx.MenuBar()
        for eachMenuData in self.menuData():
            menuLabel = eachMenuData[0]
            menuItems = eachMenuData[1:]
            menuBar.Append(self.createMenu(menuItems), menuLabel)
        self.SetMenuBar(menuBar)

    def createMenu(self, menuData):
        menu = wx.Menu()
        for eachLabel, eachStatus, eachHandler in menuData:
            if not eachLabel:
                menu.AppendSeparator()
                continue
            menuItem = menu.Append(-1, eachLabel, eachStatus)
            self.Bind(wx.EVT_MENU, eachHandler, menuItem)
        return menu

    def OnSave(self, event):
        self.InputPanel.OnSave()

    def OnLoad(self, event):
        self.InputPanel.OnLoad()
        
    def OnClear(self, event):
        self.InputPanel.OnClear()
    
    def OnCloseWindow(self, event):
        self.Close()

    def runMSR(self, event):
        self.InputPanel.OnRunMSR()

    def runKMC(self, event):
        self.InputPanel.OnRunKMC()

    def OnDestroy(self, event):
        self.Destroy()


class mainApp(wx.App):
    def OnInit(self):
        self.Frame = mainFrame(None)
        self.Frame.Show()
        return True
    

if __name__ == "__main__":
    # Change the current directory to the directory of the given script
    pwd0 = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(pwd0)
    #app = mainApp(redirect=True, filename="data/log.out")
    app = mainApp()
    app.MainLoop()