import wx
import os, sys, glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
try:
    from func.wx_opengl import WxGLScene
except:
    from wx_opengl import WxGLScene

def bold_sines(ax, bwidth):
    ax.spines['bottom'].set_linewidth(bwidth)
    ax.spines['left'].set_linewidth(bwidth)
    ax.spines['top'].set_linewidth(bwidth)
    ax.spines['right'].set_linewidth(bwidth)

class KmcFrame(wx.Frame):
    def __init__(self, title, size, inteval, glsize):
        wx.Frame.__init__(self, None, -1, title=title, size=size)
        
        self.inteval = inteval
        self.glsize = glsize
        self.font1 = {'family': 'Arial', 'weight': 'normal', 'size': 20}
        self.bwidth = 2
        self.InitUI()
        self.Center()
    
    def InitUI(self):
        self.panel = wx.Panel(self)
        self.Load_data()
        grid_sizer = wx.GridSizer(2, 2, 4, 4)
        
        plt.rc('font', size=15)
        # fig1: coverage trend
        num_surfatom = np.array([self.xyz['cov'] != 5]).sum()
        CO_cov = np.array((self.data['COads'] - self.data['COdes'] - self.data['rec']) / num_surfatom )
        O_cov = np.array((2*self.data['O2ads'] - 2*self.data['O2des'] - self.data['rec']) / num_surfatom )
        self.fig1, ax1 = plt.subplots()
        ax1.set_title('Coverage', self.font1)
        ax1.plot(self.data['step'], CO_cov, label='CO', color='k')
        ax1.plot(self.data['step'], O_cov, label='O', color='tomato')
        ax1.set_xlabel('step', self.font1)
        ax1.set_ylabel('coverage', self.font1)
        ax1.legend(fontsize=15)
        xformatter = ticker.ScalarFormatter(useMathText=True)
        xformatter.set_scientific(True)
        xformatter.set_powerlimits((-2, 2))
        ax1.xaxis.set_major_formatter(xformatter)
        ax1.tick_params(axis='both', labelsize=15, direction='in', width=self.bwidth)
        bold_sines(ax1, bwidth=self.bwidth)
        plt.subplots_adjust(left = 0.15, right = 0.9, top = 0.9, bottom = 0.2)
        plt.savefig('coverage')
        self.canvas1 = FigCanvas(self.panel, -1, self.fig1)
        grid_sizer.Add(self.canvas1, 1, wx.ALL|wx.EXPAND)

        # fig2: tof trend
        self.fig2, ax2 = plt.subplots()
        self.draw_tof(inteval=self.inteval, ax=ax2)
        ax2.xaxis.set_major_formatter(xformatter)
        bold_sines(ax2, bwidth=self.bwidth)
        plt.subplots_adjust(left = 0.15, right = 0.9, top = 0.9, bottom = 0.2)
        plt.savefig('tof')
        self.canvas2 = FigCanvas(self.panel, -1, self.fig2)
        grid_sizer.Add(self.canvas2, 1, wx.ALL|wx.EXPAND)
        
        # 创建第三个Matplotlib图像
        event = ['rec', 'Odiff', 'COdiff', 'O2des', 'O2ads', 'COdes', 'COads', ] 
        count = self.data.tail(1)[event]
        count = count.to_numpy()[0]
        # count = np.log10(count)
        self.fig3, ax3 = plt.subplots()
        ax3.set_title('Events', self.font1)
        ax3.barh(range(len(event)), count, height=0.5)
        ax3.set_xlabel('count', self.font1)
        # ax3.set_ylabel('event', self.font1)
        ax3.set_xscale('log')
        # ax3.xaxis.set_major_formatter(xformatter)
        ax3.tick_params(axis='x', labelsize=15, direction='in', width=self.bwidth) 
        ax3.set_yticks(range(len(event)), event)
        ax3.tick_params(axis='y', labelsize=15, direction='out', width=self.bwidth) 
        bold_sines(ax3, bwidth=self.bwidth)
        plt.subplots_adjust(left = 0.15, right = 0.9, top = 0.9, bottom = 0.2)        
        plt.savefig('event')
        self.canvas3 = FigCanvas(self.panel, -1, self.fig3)
        grid_sizer.Add(self.canvas3, 1, wx.ALL|wx.EXPAND)
        
        # 创建OpenGL画布
        ogl_canvas = WxGLScene(self.panel, xyzfile='ini.xyz', size=self.glsize, coltype='tof')
        grid_sizer.Add(ogl_canvas, 1, wx.ALL|wx.EXPAND)
        
        # 设置窗口的Sizer
        self.panel.SetSizer(grid_sizer)

        # 绑定事件
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.panel.Bind(wx.EVT_PAINT, self.OnPaint)
        self.panel.Bind(wx.EVT_SIZE, self.OnSize)

    def OnPaint(self, event):
        size = self.panel.GetSize()
        width, height = (size.GetWidth()-30)/2, (size.GetHeight()-32)/2
        dpi = self.panel.GetContentScaleFactor() * 96
        self.fig1.set_size_inches(width / dpi, height / dpi)
        self.fig2.set_size_inches(width / dpi, height / dpi)
        self.fig3.set_size_inches(width / dpi, height / dpi)
        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()
        event.Skip()

    def OnSize(self, event):
        size = self.panel.GetSize()
        width, height = (size.GetWidth()-30)/2, (size.GetHeight()-32)/2
        dpi = self.panel.GetContentScaleFactor() * 96
        self.fig1.set_size_inches(width / dpi, height / dpi)
        self.fig2.set_size_inches(width / dpi, height / dpi)
        self.fig3.set_size_inches(width / dpi, height / dpi)
        event.Skip()

    def OnClose(self, event):
        plt.close('all')
        self.Destroy()
        event.Skip()

    def Load_data(self):
        pwd = os.getcwd()
        self.xyz = pd.read_csv(os.path.join(pwd, 'last_one.xyz'), sep='\s+', header=None, 
                                names=['x','y','z','cov','TON','CO-TON','O2-TON'], skiprows=[0,1])
        files = glob.glob(os.path.join(pwd, '*step_rec_**.dat'))
        col = ['time', 'step', 'aj', 'COads', 'COdes', 
                'O2ads', 'O2des', 'COdiff', 'Odiff','rec']
        da = []
        for file in files:
            da.append(pd.read_csv(file, sep='\s+', header=None, names=col))
        data = pd.concat(da)
        self.data = data.sort_values(by='step', kind='mergesort')
        # record tof
        time = np.array(self.data.tail(1))[0,0]
        # print('time:\t', 1000*time, 'ms')
        with open('TOF.data', 'wt') as f:
            for i in range(len(self.xyz)):
                tof = self.xyz['TON'][i]/time
                f.write(str(tof) + '\n')

    def Tof_int(self, inteval):
        subdata = self.data[self.data['step']%inteval == 0].copy()
        subdata['dtime'] = subdata['time'].diff()
        subdata['drec'] = subdata['rec'].diff()
        return subdata
    
    def draw_tof(self, inteval, ax):
        ax.set_title('TOF', self.font1)
        subdata = self.Tof_int(inteval=inteval)
        num_surfatom = np.array([self.xyz['cov'] != 5]).sum()
        tof_trend = np.array(subdata['drec']/subdata['dtime']/num_surfatom)
        max_tof = tof_trend[1:].max()
        tof_trend[0] = 0.0
        ax.plot(subdata['step'], tof_trend, 'ro', subdata['step'], tof_trend, 'k')
        ax.set_xlabel('step', self.font1)
        ax.set_ylabel('TOF(1/s/site)', self.font1)
        ax.set_ylim(ymax = max_tof*1.1)
        formatter = ticker.ScalarFormatter(useMathText=True)
        formatter.set_scientific(True)
        formatter.set_powerlimits((-2, 2))
        ax.yaxis.set_major_formatter(formatter)
        ax.tick_params(axis='both', labelsize=15, direction='in', width=self.bwidth)


def kmc_window(inteval=1000, glsize=40):
    app2 = wx.App(False)
    app2.SetAppName('Kmc Results')
    frame = KmcFrame(title='Kmc Results', size=(800,600), inteval=inteval, glsize=glsize)
    frame.Show()
    app2.MainLoop()

if __name__ == "__main__":
    pwd0 = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(os.path.join(pwd0, '..\data'))
    kmc_window()
