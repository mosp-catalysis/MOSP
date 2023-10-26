# -*- coding: utf-8 -*-

import wx
import os, sys
import numpy as np
from matplotlib.cm import get_cmap
from matplotlib.colors import Normalize
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *

APP_TITLE = u'MOSP'

def get_color(element):
    colors = {
        'H': (1.00, 1.00, 1.00),
        'He': (0.80, 0.80, 0.80),
        'Li': (0.851, 1.00, 1.00),
        'Be': (0.761, 1.0, 1.00),
        'B': (1.00, 0.71, 0.71),
        'C': (0.565, 0.565, 0.565),
        'N': (0.188, 0.314, 0.973),
        'O': (1.00, 0.051, 0.051),
        'F': (0.565, 0.878, 0.314),
        'Na': (0.671, 0.361, 0.949),
        'Mg': (0.541, 1.00, 0.00),
        'Al': (0.749, 0.651, 0.651),
        'Si': (0.941, 0.784, 0.627),
        'P': (1.00, 0.502, 0.00),
        'S': (1.00, 1.00, 0.188),
        'Fe': (0.878, 0.400, 0.200),
        'Co': (0.941, 0.565, 0.627),
        'Ni': (0.314, 0.816, 0.314),
        'Cu': (0.784, 0.502, 0.200),
        'Zn': (0.490, 0.502, 0.690),
        'Pd': (0.000, 0.412, 0.522),
        'Ag': (0.753, 0.753, 0.753),
        'Ce': (1.00, 1.00, 0.78),
        'Pt': (0.816, 0.816, 0.878),
        'Au': (0.996, 0.698, 0.2196),
    }
    return colors.get(element, (1.00, 0.08, 0.576))

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
        coords.append(list(map(float, line.split()[1:])))
    return ele, coords

def tof_open():
    with open('TOF.data', 'r') as f:
        lines = f.readlines()
    tof = np.array([])
    for line in lines:
        tof = np.append(tof, float(line.strip('\n')))
    return tof

class WxGLScene(glcanvas.GLCanvas):
    def __init__(self, parent, xyzfile, size, coltype='ele'):
        glcanvas.GLCanvas.__init__(self, parent, -1, style=glcanvas.WX_GL_RGBA|glcanvas.WX_GL_DOUBLEBUFFER|glcanvas.WX_GL_DEPTH_SIZE)
        self.file = xyzfile
        self.coltype = coltype
        self.ele, self.coords = ini_open(self.file)
        if coltype == 'tof':
            tofs = tof_open()
            norm = Normalize(vmin=np.min(tofs), vmax=np.max(tofs))
            cmap = get_cmap("jet")
            self.color = [cmap(norm(tof)) for tof in tofs]
        self.parent = parent                                               # 父级窗口对象
        self.eye = np.array([0.0, 0.0, size])                              # 观察者的位置
        self.aim = np.array([0.0, 0.0, 0.0])                               # 观察目标(默认在坐标原点)
        self.up = np.array([0.0, 1.0, 0.0])                                # 对观察者而言的上方
        self.view = np.array([-1*size, size, -1*size, size, 1.0, size+5])  # 视景体
        
        self.size = self.GetClientSize()                        # OpenGL窗口的大小
        self.context = glcanvas.GLContext(self)                 # OpenGL上下文
        self.zoom = 1.0                                         # 视口缩放因子
        self.mpos = None                                        # 鼠标位置
        self.initGL()                                           # 画布初始化
        
        self.dist, self.phi, self.theta = self.__getposture()   # 眼睛与观察目标之间的距离、仰角、方位角
        
        self.Bind(wx.EVT_SIZE, self.onResize)                   # 绑定窗口尺寸改变事件
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onErase)        # 绑定背景擦除事件
        self.Bind(wx.EVT_PAINT, self.onPaint)                   # 绑定重绘事件
        
        self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)            # 绑定鼠标左键按下事件
        self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)                # 绑定鼠标左键弹起事件
        self.Bind(wx.EVT_RIGHT_UP, self.onRightUp)              # 绑定鼠标右键弹起事件
        self.Bind(wx.EVT_MOTION, self.onMouseMotion)            # 绑定鼠标移动事件
        self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel)         # 绑定鼠标滚轮事件
    
    def __getposture(self):
        DIST = np.sqrt(np.power((self.eye-self.aim), 2).sum())
        if DIST > 0:
            PHI = np.arcsin((self.eye[1]-self.aim[1])/DIST)
            THETA = np.arcsin((self.eye[0]-self.aim[0])/(DIST*np.cos(PHI)))
        else:
            PHI = 0.0
            THETA = 0.0
        return DIST, PHI, THETA

    def onResize(self, evt):
        """响应窗口尺寸改变事件"""
        
        if self.context:
            self.SetCurrent(self.context)
            self.size = self.GetClientSize()
            self.Refresh(False)
            
        evt.Skip()
        
    def onErase(self, evt):
        """响应背景擦除事件"""
        
        pass
        
    def onPaint(self, evt):
        """响应重绘事件"""
        
        self.SetCurrent(self.context)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)    # 清除屏幕及深度缓存
        self.drawGL()                                       # 绘图
        self.SwapBuffers()                                  # 切换缓冲区, 以显示绘制内容
        evt.Skip()
        
    def onLeftDown(self, evt):
        """响应鼠标左键按下事件"""
        
        self.CaptureMouse()
        self.mpos = evt.GetPosition()
        
    def onLeftUp(self, evt):
        """响应鼠标左键弹起事件"""

        try:
            self.ReleaseMouse()
        except:
            pass

    def onRightUp(self, evt):
        """响应鼠标右键弹起事件"""
        
        pass
        
    def onMouseMotion(self, evt):
        """响应鼠标移动事件"""
        
        if evt.Dragging() and evt.LeftIsDown():
            pos = evt.GetPosition()
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
        
    def onMouseWheel(self, evt):
        """响应鼠标滚轮事件"""
        
        if evt.WheelRotation < 0:
            self.zoom *= 1.1
            if self.zoom > 100:
                self.zoom = 100
        elif evt.WheelRotation > 0:
            self.zoom *= 0.9
            if self.zoom < 0.01:
                self.zoom = 0.01
        
        self.Refresh(False)
        
    def initGL(self):
        """初始化GL"""
        
        self.SetCurrent(self.context)

        # 设置光照
        glEnable(GL_LIGHTING) # enable lighting
        glEnable(GL_LIGHT0) # enable light 0
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 2.0, 0.0])
        #glLightfv(GL_LIGHT0, GL_SPECULAR, [0.8, 0.8, 0.8, 1.0])
        #glLightfv(GL_LIGHT0, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])
        glEnable(GL_LIGHT1) # enable light 1
        glLightfv(GL_LIGHT1, GL_POSITION, [-1.0, -1.0, -3.0, 0.0])
        glLightfv(GL_LIGHT1, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
        #glEnable(GL_LIGHT2) # enable light 1
        #glLightfv(GL_LIGHT2, GL_POSITION, [1.0, 1.0, 3.0, 0.0])
        #glLightfv(GL_LIGHT2, GL_SPECULAR, [0.4, 0.4, 0.4, 1.0])
        
        glClearColor(1,1,1,0)                                       # 设置画布背景色
        glEnable(GL_DEPTH_TEST)                                     # 开启深度测试, 实现遮挡关系        
        glDepthFunc(GL_LEQUAL)                                      # 设置深度测试函数
        glShadeModel(GL_SMOOTH)                                     # GL_SMOOTH(光滑着色)/GL_FLAT(恒定着色)
        glEnable(GL_BLEND)                                          # 开启混合        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)           # 设置混合函数
        glEnable(GL_ALPHA_TEST)                                     # 启用Alpha测试 
        glAlphaFunc(GL_GREATER, 0.05)                               # 设置Alpha测试条件为大于0.05则通过
        glFrontFace(GL_CW)                                          # 设置逆时针索引为正面(GL_CCW/GL_CW)
        glEnable(GL_LINE_SMOOTH)                                    # 开启线段反走样
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
   
    def drawGL(self):
        """绘制"""
        
        # 清除屏幕及深度缓存
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # 设置视口
        glViewport(0, 0, self.size[0], self.size[1])
        
        # 设置投影(正交)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        k = self.size[0]/self.size[1]
        if k > 1:
            glOrtho(
                self.zoom*self.view[0]*k, 
                self.zoom*self.view[1]*k, 
                self.zoom*self.view[2], 
                self.zoom*self.view[3], 
                self.view[4], self.view[5]
            )
        else:
            glOrtho(
                self.zoom*self.view[0], 
                self.zoom*self.view[1], 
                self.zoom*self.view[2]/k, 
                self.zoom*self.view[3]/k, 
                self.view[4], self.view[5]
            )
            
        # 设置视点
        gluLookAt(
            self.eye[0], self.eye[1], self.eye[2], 
            self.aim[0], self.aim[1], self.aim[2],
            self.up[0], self.up[1], self.up[2]
        )
            
        # 设置模型视图
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # ---------------------------------------------------------------
        for i in range(len(self.coords)):
            position = self.coords[i]
            glPushMatrix()
            glTranslatef(position[0], position[1], position[2])
            #sphere = gluNewQuadric()
            if self.coltype=='ele':
                color = get_color(self.ele[i])
            elif self.coltype=='tof':
                color = self.color[i]
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [color[0], color[1], color[2], 1])
            glMaterialfv(GL_FRONT, GL_SPECULAR, [0.20])
            glMaterialfv(GL_FRONT, GL_SHININESS, [8])

            sphere = gluNewQuadric()
            gluSphere(sphere, 1.5, 32, 32)
            glPopMatrix()

class mainFrame(wx.Frame):
    def __init__(self, xyzfile, size, coltype):
        wx.Frame.__init__(self, None, -1, APP_TITLE, style=wx.DEFAULT_FRAME_STYLE)
        
        self.SetBackgroundColour(wx.Colour(224, 224, 224))
        self.SetSize((800, 600))
        self.Center()
        
        self.scene = WxGLScene(self, xyzfile=xyzfile, size=size, coltype=coltype)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
    
    def OnClose(self, event):
        self.Destroy()

def glwindow(file, size=25, coltype='ele'):
    app1 = wx.App(False)
    app1.SetAppName(APP_TITLE)
    frame = mainFrame(xyzfile=file, size=size, coltype=coltype)
    frame.Show()
    app1.MainLoop()

if __name__ == "__main__":
    pwd0 = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(os.path.join(pwd0, '..\data'))
    xyzfile='D:\MOSP_tv2.0_sub_10.12\MSR\Au\ini.xyz'
    glwindow('ini.xyz', coltype='tof')
