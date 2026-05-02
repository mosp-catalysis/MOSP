# -*- coding: utf-8 -*-
"""
@author: yinglei
"""

import json
import os
import sys

import wx
import win32api

from views.input_panel import InputPanelMSR, InputPanelRKMC
from views.input_panel_ekmc import InputPanelEKMC
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
        wx.Frame.__init__(self, parent, title=APP_TITLE, size=(1000, 600))
        self.initUI()

        splitterMain = wx.SplitterWindow(self, -1)
        splitter = wx.SplitterWindow(splitterMain, -1)
        self.VisualPanel = wx.Notebook(splitter, style=wx.BK_DEFAULT)
        logPanel = LogPanel(splitter)

        self.MainInputPanel = wx.Notebook(splitterMain, style=wx.BK_DEFAULT)
        self.InputPanel_M = InputPanelMSR(self.MainInputPanel, self, logPanel)
        self.InputPanel_M.SetScrollRate(10, 10)
        self.MainInputPanel.AddPage(self.InputPanel_M, 'MSR')
        self.InputPanel_R = InputPanelRKMC(self.MainInputPanel, self, logPanel)
        self.InputPanel_R.SetScrollRate(10, 10)
        self.MainInputPanel.AddPage(self.InputPanel_R, 'RKMC')
        self.InputPanel_E = InputPanelEKMC(self.MainInputPanel, self, logPanel)
        self.InputPanel_E.SetScrollRate(10, 10)
        self.MainInputPanel.AddPage(self.InputPanel_E, 'EKMC')

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnNotebookPageChanged, self.MainInputPanel)

        self.glPanel = glPanel(self.VisualPanel, logPanel)
        self.pltPanle = pltPanel(self.VisualPanel, logPanel)
        self.pltPanle.SetScrollRate(10, 10)
        self.VisualPanel.AddPage(self.glPanel, 'Model Visual')
        self.VisualPanel.AddPage(self.pltPanle, 'Data Visual')

        self.InputPanel_M.SetFocus()

        splitterMain.SplitVertically(self.MainInputPanel, splitter)
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
        self.updateMenuForCurrentPanel()

    def initUI(self):
        if hasattr(sys, "frozen") and getattr(sys, "frozen") == "windows_exe":
            exeName = win32api.GetModuleFileName(win32api.GetModuleHandle(None))
            icon = wx.Icon(exeName, wx.BITMAP_TYPE_ICO)
        else:
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

    def OnNotebookPageChanged(self, event):
        self.updateMenuForCurrentPanel()
        event.Skip()

    def get_current_input_panel(self):
        current_page = self.MainInputPanel.GetSelection()
        if current_page == 0:
            return self.InputPanel_M
        if current_page == 1:
            return self.InputPanel_R
        if current_page == 2:
            return self.InputPanel_E
        return None

    def updateMenuForCurrentPanel(self):
        current_page = self.MainInputPanel.GetSelection()
        menuBar = self.GetMenuBar()

        if menuBar:
            run_menu = menuBar.GetMenu(1)
            run_msr_id = run_menu.FindItem("&Run MSR")
            run_kmc_id = run_menu.FindItem("&Run RKMC")
            run_ekmc_id = run_menu.FindItem("&Run EKMC")

            if run_msr_id != wx.NOT_FOUND:
                run_menu.Enable(run_msr_id, current_page == 0)
            if run_kmc_id != wx.NOT_FOUND:
                run_menu.Enable(run_kmc_id, current_page == 1)
            if run_ekmc_id != wx.NOT_FOUND:
                run_menu.Enable(run_ekmc_id, current_page == 2)

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

    def menuData(self):
        return (("&File",
                    ("&Save", "Save Input files", self.OnSave),
                    ("&Load", "Load Input files", self.OnLoad),
                    ("", "", ""),
                    ("&Quit", "Quit", self.OnCloseWindow)),
                ("&Run",
                    ("&Run MSR", "Run MSR Simulations", self.runMSR),
                    ("&Run RKMC", "Run RKMC Simulations", self.runKMC),
                    ("", "", ""),
                    ("&Run EKMC", "Run EKMC Simulations", self.runEKMC),
                ))

    def __getwildcard(self):
        return  ("JSON files (*.json)|*.json|"
                 "Text files (*.txt)|*.txt|"
                 "All files (*.*)|*.*")

    def __get_section_values(self, values, section, inner_key):
        section_values = values.get(section)
        if isinstance(section_values, dict) and section_values.get(inner_key) is not None:
            return section_values
        return values

    def OnSave(self, event):
        values = {
            'MSR': self.InputPanel_M.get_values(),
            'KMC': self.InputPanel_R.get_values(),
            'EKMC': self.InputPanel_E.get_values(),
        }
        dlg = wx.FileDialog(self, message="Save file as",
                            wildcard=self.__getwildcard(),
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            with open(path, 'w') as f:
                json.dump(values, f, indent=2)
            self.InputPanel_M.log.WriteText(f"Inputs are saved as {path}")
        dlg.Destroy()

    def OnLoad(self, event):
        dlg = wx.FileDialog(self, message="Choose a file",
                            wildcard=self.__getwildcard(),
                            style=wx.FD_OPEN | wx.FD_PREVIEW |
                            wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            with open(path, 'r') as f:
                values = json.load(f)
            self.InputPanel_M.set_values(self.__get_section_values(values, 'MSR', 'MSR'))
            self.InputPanel_R.set_values(self.__get_section_values(values, 'KMC', 'KMC'))
            self.InputPanel_E.set_values(self.__get_section_values(values, 'EKMC', 'EKMC'))
            self.InputPanel_M.log.WriteText(f"Inputs are loaded from {path}")
        dlg.Destroy()

    def OnClear(self, event):
        current_panel = self.get_current_input_panel()
        if current_panel and hasattr(current_panel, 'OnClear'):
            current_panel.OnClear()

    def runMSR(self, event):
        if self.MainInputPanel.GetSelection() == 0:
            self.InputPanel_M.OnRunMSR()

    def runKMC(self, event):
        if self.MainInputPanel.GetSelection() == 1:
            self.InputPanel_R.OnRunKMC()

    def runEKMC(self, event):
        if self.MainInputPanel.GetSelection() == 2:
            self.InputPanel_E.OnRunEKMC()

    def postRKMC(self, event):
        if self.MainInputPanel.GetSelection() == 1:
            self.InputPanel_R.PostRKMC()

    def postEKMC(self, event):
        if self.MainInputPanel.GetSelection() == 2:
            self.InputPanel_E.PostEKMC()

    def OnCloseWindow(self, event):
        self.Close()

    def OnDestroy(self, event):
        self.Destroy()


class mainApp(wx.App):
    def OnInit(self):
        self.Frame = mainFrame(None)
        self.Frame.Show()
        return True


if __name__ == "__main__":
    pwd0 = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(pwd0)
    app = mainApp()
    app.MainLoop()
