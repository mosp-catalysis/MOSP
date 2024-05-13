import wx
from utils.wx_opengl import WxGLScene


class glPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.Box)
        ogl_canvas = WxGLScene(self, xyzfile='data/INPUT/ini.xyz', size=40, coltype='ele')
        self.Box.Add(ogl_canvas, proportion = 3, flag = wx.ALL|wx.EXPAND)

        nm1 = wx.StaticBox(self, -1, '日志信息')
        nmSizer1 = wx.StaticBoxSizer(nm1, wx.VERTICAL)
        # 创建文本域
        self.multiText = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE)  # 创建一个文本控件
        self.multiText.SetInsertionPoint(0)  # 设置插入点
        nmSizer1.Add(self.multiText, 1, wx.EXPAND | wx.ALL, 10)
        #  在垂直盒子里添加StaticBoxSizer盒子
        self.Box.Add(nmSizer1, 1, wx.EXPAND | wx.ALL, 10)