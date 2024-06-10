# -*- coding: utf-8 -*-
"""
@author: yinglei
@references: https://blog.csdn.net/xufive/
"""

import os
import wx
from wx import glcanvas
import numpy as np
import pandas as pd
import OpenGL.GL as gl
import OpenGL.GLU as glu
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from views.particle import NanoParticle

WILDCARD = ("xyz files (*.xyz)|*.xyz|"
            "All files (*.*)|*.*")

FORMATTER = ticker.ScalarFormatter(useMathText=True)
# FORMATTER.set_scientific(True)
FORMATTER.set_powerlimits((-2, 2))

def SET_PLT():
    TICK_FONT_SIZE = 12
    LABEL_FONT_SIZE = 15
    AX_WIDTH = 1.5
    plt.rcParams['lines.linewidth'] = 2
    plt.rcParams['axes.linewidth'] = AX_WIDTH
    plt.rcParams['axes.labelsize'] = LABEL_FONT_SIZE
    plt.rcParams['axes.titlesize'] = LABEL_FONT_SIZE
    plt.rcParams['legend.fontsize'] = LABEL_FONT_SIZE
    plt.rcParams['legend.frameon'] = False
    plt.rcParams['xtick.labelsize'] = TICK_FONT_SIZE
    plt.rcParams['xtick.major.width'] = AX_WIDTH
    plt.rcParams['ytick.labelsize'] = TICK_FONT_SIZE
    plt.rcParams['ytick.major.width'] = AX_WIDTH
    # plt.tight_layout()

def ini_open(file):
    # Read the xyz file
    with open(file, 'r') as f:
        data = f.readlines()

    # Extract the number of atoms and the coordinates
    num_atoms = int(data[0])
    coords = []
    ele = []
    for line in data[2:]:
        info = line.strip('\n').split()
        ele.append(info[0])
        coords.append(list(map(float, line.split()[1:4])))
    return ele, coords


class glCanve(glcanvas.GLCanvas):
    def __init__(self, parent, nanoparticle : NanoParticle = None):
        glcanvas.GLCanvas.__init__(self, parent, -1, style=glcanvas.WX_GL_RGBA|glcanvas.WX_GL_DOUBLEBUFFER|glcanvas.WX_GL_DEPTH_SIZE)
        self.nanoparticle = nanoparticle
        if (self.nanoparticle):
            depth = nanoparticle.maxZ + 10
        else:
            depth = 20
        self.parent = parent

        self.eye = np.array([0.0, 0.0, depth])  # postion of observer's eyes
        self.aim = np.array([0.0, 0.0, 0.0])    # look at
        self.up = np.array([0.0, 1.0, 0.0])     # eye_up
        self.view = np.array([-1*depth, depth, -1*depth, depth, 1.0, depth+5]) # file of view-left/right/bottom/top/near/far

        self.size = self.GetClientSize()
        self.context = glcanvas.GLContext(self)
        self.zoom = 1.0
        self.mpos = None
        self.models = {}  # model list - save VBO
        self.initGL()

        self.dist, self.phi, self.theta = self.__getposture()

        self.Bind(wx.EVT_SIZE, self.onResize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onErase)
        self.Bind(wx.EVT_PAINT, self.onPaint)
        
        self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown) 
        self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
        self.Bind(wx.EVT_RIGHT_UP, self.onRightUp)
        self.Bind(wx.EVT_MOTION, self.onMouseMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel)

    def __getposture(self):
        DIST = np.sqrt(np.power((self.eye-self.aim), 2).sum())
        if DIST > 0:
            PHI = np.arcsin((self.eye[1]-self.aim[1])/DIST)
            THETA = np.arcsin((self.eye[0]-self.aim[0])/(DIST*np.cos(PHI)))
        else:
            PHI = 0.0
            THETA = 0.0
        return DIST, PHI, THETA

    def initGL(self):
        self.SetCurrent(self.context)

        # lighting set
        gl.glEnable(gl.GL_LIGHTING) # enable lighting
        gl.glEnable(gl.GL_LIGHT0) # enable light 0
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, [1.0, 1.0, 2.0, 0.0])
        # glLightfv(GL_LIGHT0, GL_SPECULAR, [0.8, 0.8, 0.8, 1.0])
        # gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        gl.glEnable(gl.GL_LIGHT1) # enable light 1
        gl.glLightfv(gl.GL_LIGHT1, gl.GL_POSITION, [-1.0, -1.0, -3.0, 1.0])
        gl.glLightfv(gl.GL_LIGHT1, gl.GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
        gl.glEnable(gl.GL_LIGHT2) # enable light 2
        gl.glLightfv(gl.GL_LIGHT2, gl.GL_POSITION, [1.0, 1.0, 3.0, 1.0])
        gl.glLightfv(gl.GL_LIGHT2, gl.GL_SPECULAR, [0.4, 0.4, 0.4, 1.0])

        gl.glClearColor(1,1,1,0)   # bg color                             # 设置画布背景色
        gl.glEnable(gl.GL_DEPTH_TEST)                                     # 开启深度测试, 实现遮挡关系        
        gl.glDepthFunc(gl.GL_LEQUAL)                                      # 设置深度测试函数
        gl.glShadeModel(gl.GL_SMOOTH)                                     # GL_SMOOTH(光滑着色)/GL_FLAT(恒定着色)
        gl.glEnable(gl.GL_BLEND)                                          # 开启混合        
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)        # 设置混合函数
        gl.glEnable(gl.GL_ALPHA_TEST)                                     # 启用Alpha测试 
        gl.glAlphaFunc(gl.GL_GREATER, 0.05)                               # 设置Alpha测试条件为大于0.05则通过
        gl.glFrontFace(gl.GL_CW)                                          # 设置逆时针索引为正面(GL_CCW/GL_CW)
        gl.glEnable(gl.GL_LINE_SMOOTH)                                    # 开启线段反走样
        gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)

    def drawGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glViewport(0, 0, self.size[0], self.size[1])

        # SET projection matrix - ortho
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        k = self.size[0]/self.size[1]
        if k > 1:
            gl.glOrtho(
                self.zoom*self.view[0]*k, 
                self.zoom*self.view[1]*k, 
                self.zoom*self.view[2], 
                self.zoom*self.view[3], 
                self.view[4], self.view[5]
            )
        else:
            gl.glOrtho(
                self.zoom*self.view[0], 
                self.zoom*self.view[1], 
                self.zoom*self.view[2]/k, 
                self.zoom*self.view[3]/k, 
                self.view[4], self.view[5]
            )

        # SET View matrix
        glu.gluLookAt(
            self.eye[0], self.eye[1], self.eye[2], 
            self.aim[0], self.aim[1], self.aim[2],
            self.up[0], self.up[1], self.up[2]
        )

        # Set model matrix
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        
        if self.nanoparticle:
            for i, position in enumerate(self.nanoparticle.positions):
                color = self.nanoparticle.colors[i]
                gl.glPushMatrix()
                gl.glTranslatef(position[0], position[1], position[2])

                gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, [color[0], color[1], color[2], 1])
                gl.glMaterialfv(gl.GL_FRONT, gl.GL_SPECULAR, [0.25])
                gl.glMaterialfv(gl.GL_FRONT, gl.GL_SHININESS, [8])

                sphere = glu.gluNewQuadric()
                glu.gluSphere(sphere, 1.5, 32, 32)
                gl.glPopMatrix()

    def onResize(self, event):
        if self.context:
            self.SetCurrent(self.context)
            self.size = self.GetClientSize()
            self.Refresh(False)
        event.Skip()

    def onErase(self, event):
        pass

    def onPaint(self, event):
        self.SetCurrent(self.context)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT|gl.GL_DEPTH_BUFFER_BIT)
        self.drawGL()
        self.SwapBuffers()
        event.Skip()

    def onLeftDown(self, event):
        self.CaptureMouse()
        self.mpos = event.GetPosition()
        
    def onLeftUp(self, event):
        try:
            self.ReleaseMouse()
        except:
            pass

    def onRightUp(self, event):
        pass
        
    def onMouseMotion(self, event):
        if event.Dragging() and event.LeftIsDown():
            pos = event.GetPosition()
            try:
                dx, dy = pos - self.mpos
            except:
                return
            self.mpos = pos
            
            WIN_W = self.size[0]
            WIN_H = self.size[1]

            self.phi += 2*np.pi*dy/WIN_H
            self.phi %= 2*np.pi
            self.theta += -2*np.pi*dx/WIN_W
            self.theta %= 2*np.pi
            r = self.dist*np.cos(self.phi)
            
            self.eye[1] = self.dist*np.sin(self.phi)
            self.eye[0] = r*np.sin(self.theta)
            self.eye[2] = r*np.cos(self.theta)
            
            if 0.5*np.pi < self.phi < 1.5*np.pi:
                self.up[1] = -1.0
            else:
                self.up[1] = 1.0
            
            self.Refresh(False)
        
    def onMouseWheel(self, event):
        if event.WheelRotation < 0:
            self.zoom *= 1.1
            if self.zoom > 100:
                self.zoom = 100
        elif event.WheelRotation > 0:
            self.zoom *= 0.9
            if self.zoom < 0.01:
                self.zoom = 0.01
        
        self.Refresh(False)

    def setNP(self, NP : NanoParticle):
        self.nanoparticle = NP
        depth = NP.maxZ + 15
        self.eye = np.array([0.0, 0.0, depth])  # postion of observer's eyes
        self.aim = np.array([0.0, 0.0, 0.0])    # look at
        self.up = np.array([0.0, 1.0, 0.0])     # eye_up
        self.view = np.array([-1*depth, depth, -1*depth, depth, 1.0, 1.5*depth]) # file of view-left/right/bottom/top/near/far

        self.dist, self.phi, self.theta = self.__getposture()
        self.Refresh(False)


class glPanel(wx.Panel):
    def __init__(self, parent, log):
        wx.Panel.__init__(self, parent)
        self.log = log
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.Box)
        # ogl_canvas = WxGLScene(self, xyzfile='data/INPUT/ini.xyz', size=40, coltype='ele')
        self.particle = None

        btnBox = wx.BoxSizer(wx.HORIZONTAL)
        self.choices = []
        self.styleCombo = wx.ComboBox(self, -1, choices=self.choices, 
                                      size=(120, -1), style=wx.CB_READONLY)
        self.styleCombo.Bind(wx.EVT_COMBOBOX, self.__OnStyleChange)
        savebtn = wx.Button(self, -1, 'Export Structure')
        savebtn.Bind(wx.EVT_BUTTON, self.__OnSave)
        btnBox.Add(wx.StaticText(self, -1, 'Color style'), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        btnBox.Add(self.styleCombo, 0, wx.ALL, 8)
        btnBox.Add(savebtn, 0, wx.ALL, 8)
        self.Box.Add(btnBox, 0, wx.ALL)
        
        self.scence = glCanve(self)
        self.Box.Add(self.scence, proportion = 3, flag = wx.ALL|wx.EXPAND)
        
    def __OnStyleChange(self, event):
        if self.particle:
            obj = event.GetEventObject()
            self.particle.setColors(coltype=obj.GetValue())
            self.scence.setNP(self.particle)

    def __OnSave(self, event):
        if self.particle:
            dlg = wx.FileDialog(self, message="Export structure as", 
                                wildcard=WILDCARD,
                                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                p = self.particle
                with open(path, 'w') as f:
                    f.write('%d\n' % (p.nAtoms))
                    f.write('%s\n' % (p.coltype))
                    if p.coltype == 'site_type':
                        for i in range(p.nAtoms):
                            f.write('%s  %.3f  %.3f  %.3f  %s\n' %
                                    (p.eles[i], p.positions[i][0], 
                                    p.positions[i][1], p.positions[i][2], 
                                    p.siteTypes[i]))
                    elif p.coltype == 'GCN':
                        for i in range(p.nAtoms):
                            f.write('%s  %.3f  %.3f  %.3f  %.3f\n' %
                                    (p.eles[i], p.positions[i][0], 
                                    p.positions[i][1], p.positions[i][2], 
                                    p.GCNs[i][0]))
                    else:
                        if p.coltype in p.TOFs.keys():
                            for i in range(p.nAtoms):
                                f.write('%s  %.3f  %.3f  %.3f  %.3e\n' %
                                        (p.eles[i], p.positions[i][0], 
                                        p.positions[i][1], p.positions[i][2],
                                        p.TOFs[p.coltype][i]))
                        else:
                            for i in range(p.nAtoms):
                                f.write('%s  %.3f  %.3f  %.3f\n' %
                                        (p.eles[i], p.positions[i][0], 
                                        p.positions[i][1], p.positions[i][2]))
                self.log.WriteText(f"Struture are saved in {path}")
            dlg.Destroy()

    def DrawMSR(self, NP : NanoParticle):
        self.choices = NP.colorlist
        self.styleCombo.Set(self.choices)
        self.styleCombo.SetValue('site_type')
        NP.setColors(coltype='site_type')
        self.scence.setNP(NP)
        self.particle = NP 

    def DrawKMC(self, NP : NanoParticle):
        self.choices = NP.colorlist
        self.styleCombo.Set(self.choices)
        self.styleCombo.SetValue('GCN')
        NP.setColors(coltype='GCN')
        self.scence.setNP(NP)
        self.particle = NP 


class pltPanel(wx.ScrolledWindow):
    def __init__(self, parent, log):
        wx.ScrolledWindow.__init__(self, parent)
        self.log = log
        self.Box = wx.BoxSizer(wx.VERTICAL)

        SET_PLT() 
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.axes.set_title(u'Data Visualization')
        self.canvas = FigureCanvas(self, -1, self.fig)
        # self.canvas.SetSize(self.GetSize())
        self.visualFlag = False

        btnBox = wx.BoxSizer(wx.HORIZONTAL)
        self.choices = ['Coverages', 'TOFs']
        self.styleCombo = wx.ComboBox(self, -1, choices=self.choices, 
                                      size=(120, -1), style=wx.CB_READONLY)
        self.styleCombo.Bind(wx.EVT_COMBOBOX, self.__OnStyleChange)
        savebtn = wx.Button(self, -1, 'Export Data')
        savebtn.Bind(wx.EVT_BUTTON, self.__OnSave)
        btnBox.Add(wx.StaticText(self, -1, 'Data'), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        btnBox.Add(self.styleCombo, 0, wx.ALL, 8)
        btnBox.Add(savebtn, 0, wx.ALL, 8)
        self.Box.Add(btnBox, 0, wx.ALL)
        self.Box.Add(self.canvas, 1, wx.EXPAND, 10)
        self.__addToolbar()

        self.SetSizer(self.Box)
        self.Bind(wx.EVT_SIZE, self.__OnResize)

    def __addToolbar(self):
        """Copied verbatim from embedding_wx2.py"""
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()
        # By adding toolbar in sizer, we are able to put it at the bottom
        # of the frame - so appearance is closer to GTK version.
        self.Box.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        # update the axes menu on the toolbar
        self.toolbar.update()

    def __getwildcard(self):
        return  ("CSV files (*.csv)|*.csv|"
                 "JSON files (*.json)|*.json|"
                 "Excel files (*.xlsx)|*.xlsx")

    def __OnStyleChange(self, event):
        if self.visualFlag:
            obj = event.GetEventObject()
            self.set_plot(obj.GetValue())

    def __OnSave(self, event):
        if self.visualFlag:
            name = self.styleCombo.GetValue()
            if name == 'Coverages':
                dfEx = self.DfCov
            elif name == 'TOFs':
                dfEx = self.DfTOF
            dlg = wx.FileDialog(self, message="Save file as", 
                                wildcard=self.__getwildcard(),
                                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                extension = os.path.splitext(path)[1]
                if extension == ".csv":
                    dfEx.to_csv(path, sep='\t')
                elif extension == ".json":
                    dfEx.to_json(path)
                elif extension == ".xlsx":
                    dfEx.to_excel(path)
                else:
                    wx.Bell()
                    self.log.WriteText(f"Unrecognized file extension: {extension}")
                    return
                self.log.WriteText(f"Data are saved in {path}")
            dlg.Destroy()            
    
    def __OnResize(self, event):
        self.canvas.SetSize(self.GetSize())
        self.Layout()
        self.canvas.Layout()

        event.Skip()
    
    def post_kmc(self, proList):
        self.DfCov = pd.DataFrame()
        self.DfTON = pd.DataFrame()
        self.DfTOF = pd.DataFrame()

        cov = pd.read_csv('OUTPUT\\rec_cov.data', sep='\s+')
        cov = cov.set_index("Time")
        self.DfCov = cov

        event = pd.read_csv('OUTPUT\\rec_event.data', sep='\s+')
        event = event.set_index("Steps")

        count = event.iloc[-1:, 1:]
        self.eventNmaes = count.keys()
        self.eventCounts = np.array(count.values.tolist()[0])

        site_path = 'OUTPUT\\rec_site_spc.data'
        with open(site_path) as f:
            self.natoms = int(f.readline().strip())
            self.nsurf = int(f.readline().strip())
            self.totTime = float(f.readline().strip())
        site_rec = pd.read_csv(site_path, sep='\s+', skiprows=3)

        self.DfTON, self.DfTOF, DfTOF_site \
            = self.__genTOF(event, site_rec, proList, 
                            self.totTime, self.nsurf)
        
        self.visualFlag = True
        self.styleCombo.SetValue("Coverages")
        self.set_plot("Coverages")

        return DfTOF_site

    @staticmethod
    def __genTOF(event : pd.DataFrame, site_rec : pd.DataFrame, 
                 prolist, totTime, nsurf=1, gap=10):
        TON = event[['Time']].copy()
        TON_site = site_rec[['cn']].copy()
        for p in prolist:
            name = p.name
            TON[name] = 0
            TON_site[name] = 0
            for evtID in p.event_gen:
                TON[name] += event.iloc[:, evtID]
                TON_site[name] += site_rec.iloc[:, evtID+5]
            for evtID in p.event_consum:
                TON[name] -= event.iloc[:, evtID]
                TON_site[name] -= site_rec.iloc[:, evtID+5]
        itv = len(event)//gap
        subTON = TON[::itv].copy()
        diffTON = subTON.diff().loc[1:]
        TOF = diffTON[['Time']].copy()
        TOF_site = site_rec[['x', 'y', 'z', 'cov', 'cn', 'gcn']].copy()
        for p in prolist:
            name = p.name
            TOF[name] = diffTON[name]/diffTON['Time']/nsurf
            TOF_site[name] = TON_site[name]/totTime
        return diffTON, TOF, TOF_site

    def set_plot(self, name):
        self.axes.clear()
        if name == "Coverages":
            self.DfCov.iloc[:, 1:].plot(
                ax=self.axes, 
                xlabel='Time (s)', ylabel='Coverages')
            self.axes.grid(linestyle='--')
            self.axes.xaxis.set_major_formatter(FORMATTER)
        elif name == "TOFs":
            self.DfTOF.iloc[:, 1:].plot(
                ax=self.axes, color='k', marker='o', mfc='r',
                xlabel='Steps', ylabel='TOF (1/s/site)')
            self.axes.grid(linestyle='--')
            self.axes.yaxis.set_major_formatter(FORMATTER)
        elif name == "Events":
            logCount = np.log10(self.eventCounts + 1)
            self.axes.barh(self.eventNmaes, logCount)
            self.axes.set_xlabel('lg(counts)')
        self.canvas.SetSize(self.GetSize())
        self.Layout()
        self.canvas.Layout()
        self.canvas.draw()
        
