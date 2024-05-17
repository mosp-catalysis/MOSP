# -*- coding: utf-8 -*-
"""
@author: yinglei
@references: https://blog.csdn.net/xufive/
"""

import wx
from wx import glcanvas
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from views.particle import NanoParticle


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
        depth = NP.maxZ + 10
        self.eye = np.array([0.0, 0.0, depth])  # postion of observer's eyes
        self.aim = np.array([0.0, 0.0, 0.0])    # look at
        self.up = np.array([0.0, 1.0, 0.0])     # eye_up
        self.view = np.array([-1*depth, depth, -1*depth, depth, 1.0, depth+5]) # file of view-left/right/bottom/top/near/far

        self.dist, self.phi, self.theta = self.__getposture()
        self.Refresh(False)


class glPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.Box)
        # ogl_canvas = WxGLScene(self, xyzfile='data/INPUT/ini.xyz', size=40, coltype='ele')
        self.scence = glCanve(self)
        
        self.Box.Add(self.scence, proportion = 3, flag = wx.ALL|wx.EXPAND)
        
        b = wx.Button(self, -1, 'Click')
        self.Box.Add(b, 0, wx.ALL, 10)
        self.Bind(wx.EVT_BUTTON, self.OnButton, b)

    def OnButton(self, event):
        if self.scence.nanoparticle:
            eles, positions = ini_open('D:\\MOSP_tv2.0_sub_10.12\\release_version\\data\\INPUT\\ini.xyz')
            NP = NanoParticle(eles, positions)
            NP.setColors(coltype='ele')
            self.scence.setNP(NP)
        else:
            eles, positions = ini_open('D:\\MOSP_tv2.0_sub_10.12\\release_version\\data\\OUTPUT\\last.xyz')
            NP = NanoParticle(eles, positions)
            NP.setColors(coltype='ele')
            self.scence.setNP(NP)
    
    def DrawNP(self, NP : NanoParticle):
        self.scence.setNP(NP)


class pltPanel(wx.ScrolledWindow):
    def __init__(self, parent):
        wx.ScrolledWindow.__init__(self, parent)
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.axes.set_title(u'Data Visualization')
        self.canvas = FigureCanvas(self, -1, self.fig)
        self.canvas.SetSize(self.GetSize())
        self.Box.Add(self.canvas, 1, wx.EXPAND|wx.ALL, 10)

        widSizer = wx.BoxSizer(wx.HORIZONTAL)
        b = wx.Button(self, -1, 'Click')
        widSizer.Add(b, 0, wx.ALL, 10)
        self.Box.Add(widSizer, 0, wx.ALL, 10)
        self.SetSizer(self.Box)
        self.Bind(wx.EVT_BUTTON, self.set_plot, b)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        pass
    
    def set_plot(self, event):
        self.axes.clear()
        scores = [89, 98, 70, 80, 60, 78, 85, 90]
        t_score = np.arange(1, len(scores) + 1, 1)
        s_score = np.array(scores)
        self.axes.plot(t_score, s_score, 'ro', t_score, s_score, 'k')
        self.axes.set_title(u'My Scores')
        self.axes.grid(True)
        self.axes.set_xlabel('T')
        self.axes.set_ylabel('score')
        self.canvas.SetSize(self.GetSize())
        self.Layout()
        self.canvas.Layout()

    def OnResize(self, event):
        self.canvas.SetSize(self.GetSize())
        self.Layout()
        self.canvas.Layout()

        event.Skip()
        
