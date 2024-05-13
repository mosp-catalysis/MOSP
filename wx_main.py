# -*- coding: utf-8 -*-
"""
@author: yinglei
"""

import wx
import os
import sys  
import win32api
from views.input_panel import InputPanel
from views.gl_panel import glPanel

APP_TITLE = 'MOSP'
APP_ICON = 'logo.ico'

class mainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title=APP_TITLE)
        self.initUI()

        self.splitter = wx.SplitterWindow(self, -1)
        self.InpPanel = InputPanel(self.splitter)
        self.InpPanel.SetScrollRate(10, 10)
        self.InpPanel.SetFocus()

        self.GlPanel = glPanel(self.splitter)

        self.splitter.SplitVertically(self.InpPanel, self.GlPanel) 
        self.splitter.SetSashGravity(0.618)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(8)
        sizer.Add(self.splitter, 1, flag=wx.EXPAND)
        self.SetSizer(sizer)
        sizer.AddSpacer(8)

        self.createMenuBar()

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
        pass

    def OnLoad(self, event):
        pass
    
    def OnCloseWindow(self, event):
        self.Close()

    def runMSR(self, event):
        pass

    def runKMC(self, event):
        pass


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