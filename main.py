# -*- coding: utf-8 -*-
"""
@author: yinglei
"""

import wx
import os
import sys  
import win32api
from views.input_panel import InputPanel
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

        # 左右Splitter - 左input, 右visual+log
        splitterMain = wx.SplitterWindow(self, -1)
        splitter = wx.SplitterWindow(splitterMain, -1)
        self.VisualPanel = wx.Notebook(splitter, style=wx.BK_DEFAULT)
        logPanel = LogPanel(splitter)

        self.MainInputPanel = wx.Notebook(splitterMain, style=wx.BK_DEFAULT)
        self.InputPanel_R = InputPanel(self.MainInputPanel, self, logPanel)
        self.InputPanel_R.SetScrollRate(10, 10)
        self.MainInputPanel.AddPage(self.InputPanel_R, 'MSR+RKMC')
        self.InputPanel_E = InputPanelEKMC(self.MainInputPanel, self, logPanel)
        self.InputPanel_E.SetScrollRate(10, 10)
        self.MainInputPanel.AddPage(self.InputPanel_E, 'EKMC')

        # 绑定Notebook页面切换事件
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnNotebookPageChanged, self.MainInputPanel)

        self.glPanel = glPanel(self.VisualPanel, logPanel)
        self.pltPanle = pltPanel(self.VisualPanel, logPanel)
        self.pltPanle.SetScrollRate(10, 10)
        self.VisualPanel.AddPage(self.glPanel, 'Model Visual')
        self.VisualPanel.AddPage(self.pltPanle, 'Data Visual')

        self.InputPanel_R.SetFocus()

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
        # 初始时根据当前页面更新菜单状态
        self.updateMenuForCurrentPanel()

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

    def OnNotebookPageChanged(self, event):
        """当Notebook页面切换时触发"""
        self.updateMenuForCurrentPanel()
        event.Skip()
    
    def get_current_input_panel(self):
        """获取当前激活的InputPanel"""
        current_page = self.MainInputPanel.GetSelection()
        if current_page == 0:
            return self.InputPanel_R
        elif current_page == 1:
            return self.InputPanel_E
        return None
    
    def updateMenuForCurrentPanel(self):
        """根据当前面板更新菜单项的启用状态"""
        current_page = self.MainInputPanel.GetSelection()
        menuBar = self.GetMenuBar()
        
        if menuBar:
            run_menu = menuBar.GetMenu(1)  # 第二个菜单是Run
            # 获取所有菜单项ID
            run_msr_id = run_menu.FindItem("&Run MSR")
            run_kmc_id = run_menu.FindItem("&Run RKMC")
            run_ekmc_id = run_menu.FindItem("&Run EKMC")

            if current_page == 0:  # MSR+RKMC页面
                # 启用MSR和KMC，禁用EKMC
                if run_msr_id != wx.NOT_FOUND:
                    run_menu.Enable(run_msr_id, True)
                if run_kmc_id != wx.NOT_FOUND:
                    run_menu.Enable(run_kmc_id, True)
                if run_ekmc_id != -1:
                    run_menu.Enable(run_ekmc_id, False)
            
            elif current_page == 1:  # EKMC页面
                # 禁用MSR和KMC，启用EKMC
                if run_msr_id != wx.NOT_FOUND:
                    run_menu.Enable(run_msr_id, False)
                if run_kmc_id != wx.NOT_FOUND:
                    run_menu.Enable(run_kmc_id, False)
                if run_ekmc_id != -1:
                    run_menu.Enable(run_ekmc_id, True)

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
                    # ("&Clear", "Clear Inputs", self.OnClear),
                    ("", "", ""),
                    ("&Quit", "Quit", self.OnCloseWindow)),
                ("&Run",
                    ("&Run MSR", "Run MSR Simulations", self.runMSR),
                    ("&Run RKMC", "Run RKMC Simulations", self.runKMC),
                    ("", "", ""),
                    ("&Run EKMC", "Run EKMC Simulations", self.runEKMC),
                ))

    # 通用的Save/Load函数
    def OnSave(self, event):
        current_panel = self.get_current_input_panel()
        # print("Save ", current_panel)
        if current_panel and hasattr(current_panel, 'OnSave'):
            current_panel.OnSave()
    
    def OnLoad(self, event):
        current_panel = self.get_current_input_panel()
        # print("Load ", current_panel)
        if current_panel and hasattr(current_panel, 'OnLoad'):
            current_panel.OnLoad()
    
    def OnClear(self, event):
        current_panel = self.get_current_input_panel()
        # print("Clear ", current_panel)
        if current_panel and hasattr(current_panel, 'OnClear'):
            current_panel.OnClear()
    
    # 专门的运行函数
    def runMSR(self, event):
        """只在MSR+RKMC页面有效"""
        if self.MainInputPanel.GetSelection() == 0:  # MSR+RKMC页面
            self.InputPanel_R.OnRunMSR()
    
    def runKMC(self, event):
        """只在MSR+RKMC页面有效"""
        if self.MainInputPanel.GetSelection() == 0:  # MSR+RKMC页面
            self.InputPanel_R.OnRunKMC()
    
    def runEKMC(self, event):
        """只在EKMC页面有效"""
        if self.MainInputPanel.GetSelection() == 1:  # EKMC页面
            self.InputPanel_E.OnRunEKMC()
    
    def OnCloseWindow(self, event):
        self.Close()

    # def postKMC(self, event):
    #     self.InputPanel_R.PostKmc()

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