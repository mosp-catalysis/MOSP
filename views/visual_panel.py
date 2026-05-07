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
try:
    import OpenGL.GL as gl
    import OpenGL.GLU as glu
    OPENGL_IMPORT_ERROR = None
except Exception as exc:
    gl = None
    glu = None
    OPENGL_IMPORT_ERROR = exc
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
        if OPENGL_IMPORT_ERROR is not None:
            raise RuntimeError(f"PyOpenGL is unavailable: {OPENGL_IMPORT_ERROR}")
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
        self.context = None  # 延迟初始化
        self._gl_initialized = False
        self.zoom = 1.0
        self.mpos = None
        self.models = {}
        self._quadric = None  # 缓存quadric对象
        self._refresh_timer = None

        self.dist, self.phi, self.theta = self.__getposture()

        self.Bind(wx.EVT_SIZE, self.onResize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onErase)
        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.Bind(wx.EVT_SHOW, self.onShow)  # 添加显示事件
        
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

    def onShow(self, event):
        """窗口显示时初始化GL"""
        if event.IsShown() and not self._gl_initialized:
            wx.CallLater(100, self.delayedGLInit)
        event.Skip()

    def delayedGLInit(self):
        """Delayed GL initialization."""
        if not self._gl_initialized and self.IsShown():
            try:
                self.context = glcanvas.GLContext(self)
                self.SetCurrent(self.context)
                self.initGL()
                self._gl_initialized = True
                wx.CallLater(50, self.Refresh, False)
            except Exception as e:
                print(f"GL initialization failed: {e}")
                callback = getattr(self.parent, "onGLInitFailed", None)
                if callback:
                    callback(e)

    def onResize(self, event):
        """安全的调整尺寸处理"""
        if self._gl_initialized and self.IsShown() and self.context:
            try:
                self.SetCurrent(self.context)
                self.size = self.GetClientSize()
                # 只在尺寸有效时刷新
                if self.size.width > 0 and self.size.height > 0:
                    self.Refresh(False)
            except wx._core.wxAssertionError:
                # 设置上下文失败，延迟处理
                wx.CallLater(50, self.retryResize)
        event.Skip()

    def retryResize(self):
        """重试调整尺寸"""
        if self._gl_initialized and self.IsShown() and self.context:
            try:
                self.SetCurrent(self.context)
                self.size = self.GetClientSize()
                if self.size.width > 0 and self.size.height > 0:
                    self.Refresh(False)
            except:
                pass

    def onPaint(self, event):
        """安全的绘制处理"""
        if not self._gl_initialized or not self.IsShown() or not self.context:
            event.Skip()
            return
        try:
            self.SetCurrent(self.context)
            # 验证尺寸
            if self.size.width <= 0 or self.size.height <= 0:
                self.size = self.GetClientSize()
                if self.size.width <= 0 or self.size.height <= 0:
                    event.Skip()
                    return
                    
            gl.glClear(gl.GL_COLOR_BUFFER_BIT|gl.GL_DEPTH_BUFFER_BIT)
            self.drawGL()
            self.SwapBuffers()
        except wx._core.wxAssertionError:
            # 上下文设置失败，延迟重绘
            wx.CallLater(50, self.Refresh, False)
        except Exception as e:
            print(f"渲染错误: {e}")
        finally:
            event.Skip()

    def initGL(self):
        self.SetCurrent(self.context)

        if self._quadric is None:
            self._quadric = glu.gluNewQuadric()

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
        current_size = self.GetClientSize()
        if current_size.width > 0 and current_size.height > 0:
            self.size = current_size
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
        
        if self.nanoparticle and self._quadric:
            for i, position in enumerate(self.nanoparticle.positions):
                color = self.nanoparticle.colors[i]
                gl.glPushMatrix()
                gl.glTranslatef(position[0], position[1], position[2])

                gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT_AND_DIFFUSE, [color[0], color[1], color[2], 1])
                gl.glMaterialfv(gl.GL_FRONT, gl.GL_SPECULAR, [0.25])
                gl.glMaterialfv(gl.GL_FRONT, gl.GL_SHININESS, [8])

                # 使用缓存的quadric而不是每次创建新的
                glu.gluSphere(self._quadric, 1.5, 32, 32)
                gl.glPopMatrix()

    def onErase(self, event):
        pass

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
        if not self._gl_initialized and self.IsShown():
            self.delayedGLInit()
        else:
            self.Refresh(False)

    # 添加清理方法
    def cleanup(self):
        """清理GL资源"""
        if self._quadric and glu is not None:
            glu.gluDeleteQuadric(self._quadric)
            self._quadric = None
        self._gl_initialized = False

    def __del__(self):
        self.cleanup()    


class Particle2DCanvas(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.nanoparticle = None
        self.zoom = 1.0
        self.rotation = np.array([0.0, 0.0])
        self._last_mouse_pos = None
        self._data_center = np.array([0.0, 0.0, 0.0])
        self._base_scale = 1.0
        self.SetBackgroundColour("white")
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetMinSize((240, 180))

        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onErase)
        self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
        self.Bind(wx.EVT_MOTION, self.onMouseMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel)
        self.Bind(wx.EVT_RIGHT_UP, self.onResetView)
        self.Bind(wx.EVT_LEFT_DCLICK, self.onResetView)

    def setNP(self, NP: NanoParticle):
        self.nanoparticle = NP
        self.fitView(reset_rotation=True)
        self.Refresh(False)

    def fitView(self, reset_rotation=True):
        if not self.nanoparticle or self.nanoparticle.nAtoms == 0:
            self._data_center = np.array([0.0, 0.0, 0.0])
            self._base_scale = 1.0
            self.zoom = 1.0
            if reset_rotation:
                self.rotation = np.array([0.0, 0.0])
            return

        positions = np.asarray(self.nanoparticle.positions, dtype=float)
        min_xyz = positions.min(axis=0)
        max_xyz = positions.max(axis=0)
        self._data_center = (min_xyz + max_xyz) / 2.0
        centered = positions - self._data_center
        radius = max(float(np.linalg.norm(centered, axis=1).max()), 1.0)
        size = self.GetClientSize()
        width = max(size.width, 1)
        height = max(size.height, 1)
        padding = 32
        self._base_scale = max(
            1.0,
            min((width - 2 * padding) / (2 * radius),
                (height - 2 * padding) / (2 * radius))
        )
        self.zoom = 1.0
        if reset_rotation:
            self.rotation = np.array([0.0, 0.0])

    def _project_positions(self, positions):
        centered = positions - self._data_center
        yaw, pitch = self.rotation
        cy, sy = np.cos(yaw), np.sin(yaw)
        cp, sp = np.cos(pitch), np.sin(pitch)
        rot_y = np.array([[cy, 0.0, sy],
                          [0.0, 1.0, 0.0],
                          [-sy, 0.0, cy]])
        rot_x = np.array([[1.0, 0.0, 0.0],
                          [0.0, cp, -sp],
                          [0.0, sp, cp]])
        return centered @ rot_y.T @ rot_x.T

    def onResize(self, event):
        if self.nanoparticle:
            self.fitView(reset_rotation=False)
        self.Refresh(False)
        event.Skip()

    def onErase(self, event):
        pass

    def onPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.Brush("white"))
        dc.Clear()

        size = self.GetClientSize()
        width = max(size.width, 1)
        height = max(size.height, 1)

        if not self.nanoparticle:
            dc.SetTextForeground(wx.Colour(120, 120, 120))
            msg = "2D view is ready. Run a module to display the structure."
            tw, th = dc.GetTextExtent(msg)
            dc.DrawText(msg, max((width - tw) // 2, 8), max((height - th) // 2, 8))
            return

        positions = np.asarray(self.nanoparticle.positions, dtype=float)
        colors = np.asarray(self.nanoparticle.colors)
        if positions.size == 0:
            return

        rotated = self._project_positions(positions)
        scale = self._base_scale * self.zoom
        screen_center = np.array([width / 2.0, height / 2.0])
        radius = int(max(2, min(14, scale * 1.5)))
        order = np.argsort(rotated[:, 2]) if rotated.shape[1] > 2 else np.arange(len(rotated))

        dc.SetPen(wx.Pen(wx.Colour(95, 95, 95), 1))
        for idx in order:
            sx = screen_center[0] + rotated[idx, 0] * scale
            sy = screen_center[1] - rotated[idx, 1] * scale
            color = colors[idx]
            red = int(max(0, min(255, float(color[0]) * 255)))
            green = int(max(0, min(255, float(color[1]) * 255)))
            blue = int(max(0, min(255, float(color[2]) * 255)))
            dc.SetBrush(wx.Brush(wx.Colour(red, green, blue)))
            dc.DrawCircle(int(sx), int(sy), radius)

    def onLeftDown(self, event):
        self.CaptureMouse()
        pos = event.GetPosition()
        self._last_mouse_pos = np.array([pos.x, pos.y], dtype=float)

    def onLeftUp(self, event):
        self._last_mouse_pos = None
        if self.HasCapture():
            self.ReleaseMouse()

    def onMouseMotion(self, event):
        if event.Dragging() and event.LeftIsDown() and self._last_mouse_pos is not None:
            pos = event.GetPosition()
            current = np.array([pos.x, pos.y], dtype=float)
            dx, dy = current - self._last_mouse_pos
            self.rotation[0] += dx * 0.01
            self.rotation[1] += dy * 0.01
            limit = np.pi * 0.49
            self.rotation[1] = max(-limit, min(limit, self.rotation[1]))
            self._last_mouse_pos = current
            self.Refresh(False)

    def onMouseWheel(self, event):
        if event.WheelRotation > 0:
            self.zoom *= 1.15
        elif event.WheelRotation < 0:
            self.zoom /= 1.15
        self.zoom = max(0.05, min(50.0, self.zoom))
        self.Refresh(False)

    def onResetView(self, event):
        self.fitView(reset_rotation=True)
        self.Refresh(False)


class glPanel(wx.Panel):
    def __init__(self, parent, log):
        wx.Panel.__init__(self, parent)
        self.log = log
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.Box)
        self.SetBackgroundColour("white")
        self.particle = None
        self.scence = None
        self.render3d = False

        btnBox = wx.BoxSizer(wx.HORIZONTAL)
        self.choices = []
        self.styleCombo = wx.ComboBox(self, -1, choices=self.choices,
                                      size=(120, -1), style=wx.CB_READONLY)
        self.styleCombo.Bind(wx.EVT_COMBOBOX, self.__OnStyleChange)
        savebtn = wx.Button(self, -1, 'Export Structure')
        savebtn.Bind(wx.EVT_BUTTON, self.__OnSave)
        self.render3dBtn = wx.ToggleButton(self, -1, '3D Render: OFF', size=(130, -1))
        self.render3dBtn.SetValue(False)
        self.render3dBtn.Bind(wx.EVT_TOGGLEBUTTON, self.__OnRender3DToggle)
        self.__UpdateRenderButtonAppearance()
        btnBox.Add(wx.StaticText(self, -1, 'Color style'), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        btnBox.Add(self.styleCombo, 0, wx.ALL, 8)
        btnBox.Add(savebtn, 0, wx.ALL, 8)
        btnBox.AddSpacer(16)
        btnBox.Add(self.render3dBtn, 0, wx.ALL, 8)
        self.Box.Add(btnBox, 0, wx.ALL)

        self.canvas2d = Particle2DCanvas(self)
        self.Box.Add(self.canvas2d, proportion=3, flag=wx.ALL|wx.EXPAND)

    def __OnRender3DToggle(self, event):
        self.render3d = self.render3dBtn.GetValue()
        self.__UpdateRenderButtonAppearance()
        self.__UpdateActiveCanvas()

    def __UpdateRenderButtonAppearance(self):
        if self.render3d:
            self.render3dBtn.SetLabel('3D Render: ON')
            self.render3dBtn.SetBackgroundColour(wx.Colour(56, 118, 191))
            self.render3dBtn.SetForegroundColour(wx.Colour(255, 255, 255))
        else:
            self.render3dBtn.SetLabel('3D Render: OFF')
            self.render3dBtn.SetBackgroundColour(wx.Colour(235, 235, 235))
            self.render3dBtn.SetForegroundColour(wx.Colour(30, 30, 30))
        self.render3dBtn.Refresh()

    def __Ensure3DCanvas(self):
        if self.scence:
            return True
        try:
            self.scence = glCanve(self)
            self.scence.Hide()
            self.Box.Add(self.scence, proportion=3, flag=wx.ALL|wx.EXPAND)
            return True
        except Exception as exc:
            self.onGLInitFailed(exc)
            return False

    def __UpdateActiveCanvas(self):
        if self.render3d:
            if not self.__Ensure3DCanvas():
                return
            self.canvas2d.Hide()
            self.scence.Show()
            if self.particle:
                self.scence.setNP(self.particle)
        else:
            if self.scence:
                self.scence.Hide()
            self.canvas2d.Show()
            if self.particle:
                self.canvas2d.setNP(self.particle)
        self.Layout()

    def onGLInitFailed(self, exc):
        self.render3d = False
        self.render3dBtn.SetValue(False)
        self.__UpdateRenderButtonAppearance()
        if self.scence:
            self.scence.Hide()
        self.canvas2d.Show()
        if self.log:
            self.log.WriteText(f"3D Render disabled: OpenGL initialization failed ({exc})")
        self.Layout()

    def __RefreshParticleView(self):
        if not self.particle:
            return
        if self.render3d:
            if self.__Ensure3DCanvas():
                self.scence.setNP(self.particle)
        else:
            self.canvas2d.setNP(self.particle)

    def __OnStyleChange(self, event):
        if self.particle:
            obj = event.GetEventObject()
            self.particle.setColors(coltype=obj.GetValue())
            self.__RefreshParticleView()

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
                    elif p.coltype == 'CN':
                        for i in range(p.nAtoms):
                            f.write('%s  %.3f  %.3f  %.3f  %.3f\n' %
                                    (p.eles[i], p.positions[i][0],
                                    p.positions[i][1], p.positions[i][2],
                                    p.CNs[i][0]))
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

    def __SetParticle(self, NP: NanoParticle, default_style: str):
        self.choices = NP.colorlist
        self.styleCombo.Clear()
        self.styleCombo.Set(self.choices)
        self.styleCombo.SetValue(default_style)
        NP.setColors(coltype=default_style)
        self.particle = NP
        self.__RefreshParticleView()

    def DrawMSR(self, NP : NanoParticle):
        self.__SetParticle(NP, 'site_type')

    def DrawKMC(self, NP : NanoParticle):
        self.__SetParticle(NP, 'GCN')

    def DrawEKMC(self, NP : NanoParticle):
        self.__SetParticle(NP, 'CN')


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

        btnBox = wx.BoxSizer(wx.HORIZONTAL)
        self.choices = []  # 初始为空，等待运行后设置
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

        self.visualFlag = False
        self.DfCov = pd.DataFrame()
        self.DfTON = pd.DataFrame()
        self.DfTOF = pd.DataFrame()

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

    def __OnStyleChange(self, event):
        if self.visualFlag:
            obj = event.GetEventObject()
            self.set_plot(obj.GetValue())

    def update_plot_choices(self, choices, default_choice=None):
        """更新绘图选项并刷新ComboBox"""
        self.choices = choices
        
        # 保存当前选择
        current_selection = self.styleCombo.GetValue()
        
        # 清除并重新设置选项
        self.styleCombo.Clear()
        for choice in choices:
            self.styleCombo.Append(choice)
        
        # 设置默认选择
        if default_choice and default_choice in choices:
            self.styleCombo.SetValue(default_choice)
            self.set_plot(default_choice)
        elif current_selection in choices:
            self.styleCombo.SetValue(current_selection)
        elif choices:  # 如果列表不为空
            self.styleCombo.SetSelection(0)
            self.set_plot(self.styleCombo.GetValue())
    
    def post_rkmc(self, proList):
        """RKMC运行后的处理"""
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
        # 更新绘图选项：RKMC
        rkmc_choices = ['Coverages', 'TOFs']
        self.update_plot_choices(rkmc_choices, "Coverages")
        
        # 确保绘图
        if "Coverages" in rkmc_choices:
            self.set_plot("Coverages")

        return DfTOF_site

    def post_ekmc(self):
        """EKMC运行后的处理"""
        cov = pd.read_csv('EKMC-OUTPUT\\rec_cov.data', sep='\s+')
        if 'nSurfs' in cov.columns:
            cov = cov.drop('nSurfs', axis=1)
        cov = cov.set_index("Time")
        self.DfCov = cov

        site_path = 'EKMC-OUTPUT\\final_stru.xyz'
        with open(site_path) as f:
            natoms = int(f.readline().strip())
        final_stru_coors = pd.read_csv(site_path, sep='\s+', skiprows=1)

        self.visualFlag = True
        
        # 更新绘图选项：EKMC
        ekmc_choices = ['Coverages']  # 初始只有Coverages，以后可以平均配位数等
        self.update_plot_choices(ekmc_choices, "Coverages")

        if "Coverages" in ekmc_choices:
            self.set_plot("Coverages")
        
        return final_stru_coors

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
                xlabel='Time (s)', ylabel='Coverage')
            self.axes.grid(linestyle='--')
            self.axes.xaxis.set_major_formatter(FORMATTER)
        elif name == "TOFs":
            self.DfTOF.iloc[:, 1:].plot(
                ax=self.axes, marker='o', mfc='#FFF5E3',
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
        
