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

APP_TITLE = 'MOSP'
APP_ICON = 'logo.ico'

class printLog:
    def __init__(self):
        pass

    def write(self, txt):
        print('%s' % txt)

    def WriteText(self, txt):
        print('%s' % txt)


class mainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title=APP_TITLE)
        self.initUI()
        log = printLog()

        self.splitter = wx.SplitterWindow(self, -1)
        self.InputPanel = InputPanel(self.splitter, log)
        self.InputPanel.SetScrollRate(10, 10)
        self.InputPanel.SetFocus()

        VisualPanel = wx.Notebook(self.splitter, style=wx.BK_DEFAULT)
        self.glPanel = glPanel(VisualPanel)
        self.pltPanle = pltPanel(VisualPanel)
        self.pltPanle.SetScrollRate(10, 10)
        VisualPanel.AddPage(self.glPanel, 'Model Visual')
        VisualPanel.AddPage(self.pltPanle, 'Data Visual')

        self.splitter.SplitVertically(self.InputPanel, VisualPanel) 
        self.splitter.SetSashGravity(0.618)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(8)
        sizer.Add(self.splitter, 1, flag=wx.EXPAND)
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
        self.SetBackgroundColour('white')
        self.Center()
        self.Maximize(True)

    def menuData(self):
        return (("&File",
                    ("&Save", "Save Input files", self.OnSave),
                    ("&Load", "Load Input files", self.OnLoad),
                    ("&Clear", "Clear Inputs", self.OnClear),
                    ("", "", ""),
                    ("&Quit", "Quit", self.OnCloseWindow)),
                ("&Run",
                    ("&Run MSR", "Run MSR Simulations", self.runMSR),
                    ("&Run KMC", "Run KMC Simulations", self.runMSR)))

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
        NP = self.InputPanel.OnRunMSR()
        if NP:
            self.glPanel.DrawNP(NP)

    def runKMC(self, event):
        pass

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