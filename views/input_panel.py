"""
@author: yinglei
"""

import wx
import json
import time
import bidict
import numpy as np
import os
import subprocess

try:
    from utils.msr import Wulff
    from utils.kmc_oi import writeKmcInp
except:
    pass

try:
    import views.onoffbutton as oob
    from views.validator import CharValidator
    from views.particle import NanoParticle
    from views.dataclass import Specie, Product, Event
except:
    import onoffbutton as oob
    from validator import CharValidator
    from particle import NanoParticle
    from dataclass import Specie, Product, Event

BG_COLOR = 'white'
POP_BG_COLOR = '#FFFAEF'
WARNING_COLOR = '#D6B4FD'
FIX_COLOR = '#B0C4DE'

def GET_FONT():
    FONT = wx.Font(
        12, wx.FONTFAMILY_DEFAULT,
        wx.FONTSTYLE_NORMAL,
        wx.FONTWEIGHT_NORMAL,
        False, 'Calibri')
    return FONT

def GET_INFO_BMP():
    # INFO_BMP = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16))
    # INFO_IMG = wx.Image("assets/blue_info.png", wx.BITMAP_TYPE_PNG)
    # INFO_IMG.Rescale(16, 16)
    INFO_BMP = wx.Bitmap("assets/blue_info.png", wx.BITMAP_TYPE_PNG)
    return INFO_BMP


class InputPanel(wx.ScrolledWindow):
    def __init__(self, parent, topWin, log=None):
        wx.ScrolledWindow.__init__(self, parent)
        self.topWin = topWin
        self.log = log
        self.infoBar = wx.InfoBar(self)
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.Box)
        self.Box.Add(self.infoBar, 0, wx.EXPAND, 5)

        self.digitValidator = CharValidator('NUM_ONLY', log=self.log)
        self.posDigitValidator = CharValidator('POS_NUM_ONLY', log=self.log)

        self.particle = None
        self.entries = {}
        self.values = {}
        self.__InitCommon()
        self.__InitOnoff()
        self.__InitMSR()
        self.__InitKMC()
    
    def __InitCommon(self):
        # dict-key, unit, type, combolist
        items = [("Element", '', 'Entry', ''),
                  ("Lattice constant", ' (\u00C5)', 'Entry', 'POS_NUM_ONLY'),
                  ("Crystal structure", '', 'Combobox', ('FCC', 'BCC')),
                  ("Pressure", ' (Pa)', 'Entry', 'POS_NUM_ONLY'), 
                  ("Temperature", ' (K)', 'Entry', 'POS_NUM_ONLY'),]
        gridSz =  wx.FlexGridSizer(3, 6, 8, 16)
        for (label, unit, widget_type, dlc) in items:
            gridSz.Add(wx.StaticText(self, label=label+unit), 
                       0, wx.ALIGN_CENTER)
            if widget_type == 'Entry':
                wgt = wx.TextCtrl(self, -1, size=(120, -1), style=wx.TE_CENTRE)
                wgt.SetValidator(self.posDigitValidator)
            elif widget_type == 'Combobox':
                wgt = wx.ComboBox(self, -1, choices=dlc, value=dlc[0], 
                                  size=(120, -1), style=wx.CB_READONLY|wx.TE_CENTER)
            gridSz.Add(wgt, 0, wx.ALIGN_CENTER)
            self.entries[label] = wgt

        self.Box.AddSpacer(8)
        self.Box.Add(gridSz, 0, wx.EXPAND, 5)

    def __InitOnoff(self):
        font = GET_FONT()
        boxh = wx.BoxSizer(wx.HORIZONTAL)
        self.msrOnoff = oob.OnOffButton(self, -1, "Enabling MSR",
                                        initial = 1, 
                                        name="msrOnoff")
        self.msrOnoff.SetBackgroundColour(BG_COLOR)
        self.msrOnoff.SetFont(font)
        self.kmcOnoff = oob.OnOffButton(self, -1, "Enabling KMC",
                                        initial = 1, 
                                        name="kmcOnoff")
        self.kmcOnoff.SetBackgroundColour(BG_COLOR)
        self.kmcOnoff.SetFont(font)
        self.msrRunBtn = wx.Button(self, -1, "Run MSR")
        self.msrRunBtn.Bind(wx.EVT_BUTTON, self.OnRunMSR)
        self.kmcRunBtn = wx.Button(self, -1, "Run KMC")
        self.kmcRunBtn.Bind(wx.EVT_BUTTON, self.OnRunKMC)
        boxh.Add(self.msrOnoff, 0, wx.ALL, 8)
        boxh.Add(self.msrRunBtn, 0, wx.ALL, 8)
        boxh.AddSpacer(40)
        boxh.Add(self.kmcOnoff, 0, wx.ALL, 8)
        boxh.Add(self.kmcRunBtn, 0, wx.ALL, 8)
        self.Bind(oob.EVT_ON, self.__SwOn)
        self.Bind(oob.EVT_OFF, self.__SwOff)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.__SwColl)
        self.entries['flag_MSR'] = self.msrOnoff
        self.entries['flag_KMC'] = self.kmcOnoff
        self.Box.Add(boxh, 0, wx.ALL|wx.EXPAND)

        self.kmcOnoff.SetValue(0)
        self.kmcRunBtn.Disable()
    
    def __InitMSR(self):
        self.msrPane = MsrPanel(self)
        self.msrPane.Collapse(False)
        self.Box.Add(self.msrPane, 0, wx.ALL|wx.EXPAND)

    def __InitKMC(self):
        self.kmcPane = KmcPanel(self)
        #self.kmcPane.Collapse(False)
        self.Box.Add(self.kmcPane, 0, wx.ALL|wx.EXPAND)

    def __SwOn(self, event):
        obj = event.GetEventObject()
        if obj.Name == 'msrOnoff':
            if self.msrPane.IsCollapsed:
                self.msrPane.Collapse(False)
                self.OnInnerSizeChanged()
            self.msrRunBtn.Enable()
        elif obj.Name == 'kmcOnoff':
            if self.kmcPane.IsCollapsed:
                self.kmcPane.Collapse(False)
                self.OnInnerSizeChanged()
            self.kmcRunBtn.Enable()
        event.Skip()
    
    def __SwOff(self, event):
        obj = event.GetEventObject()
        if obj.Name == 'msrOnoff':
            if self.msrPane.IsExpanded:
                self.msrPane.Collapse(True)
                self.Layout()
            self.msrRunBtn.Disable()
        elif obj.Name == 'kmcOnoff':
            if self.kmcPane.IsExpanded:
                self.kmcPane.Collapse(True)
                self.Layout()
            self.kmcRunBtn.Disable()
        event.Skip()

    def __SwColl(self, event):
        """ obj = event.GetEventObject()
        if obj.Name == 'msr':
            self.msrOnoff.SetValue(self.msrPane.IsExpanded())
        elif obj.Name == 'kmc':
            self.kmcOnoff.SetValue(self.kmcPane.IsExpanded()) """
        # print(event.GetEventObject().Name)
        self.OnInnerSizeChanged()

    def __getwildcard(self):
        return  ("JSON files (*.json)|*.json|"
                 "Text files (*.txt)|*.txt|"
                 "All files (*.*)|*.*")

    def __save(self):
        for key, widget in self.entries.items():
            self.values[key] = widget.GetValue()
        if self.values['flag_MSR']:
            self.values['MSR'] = self.msrPane.OnSave()
        if self.values['flag_KMC']:
            self.values['KMC'] = self.kmcPane.OnSave()

    def OnSave(self):
        self.__save()
        dlg = wx.FileDialog(self, message="Save file as", 
                            wildcard=self.__getwildcard(),
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            with open(path, 'w') as f:
                json.dump(self.values, f, indent=2)
            self.log.WriteText(f"Inputs are saved as {path}")
        dlg.Destroy()

    def OnLoad(self):
        dlg = wx.FileDialog(self, message="Choose a file",
                            wildcard=self.__getwildcard(),
                            style=wx.FD_OPEN | wx.FD_PREVIEW |
                            wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.log.WriteText(f"Loading")
            path = dlg.GetPath()
            with open(path, 'r') as f:
                values = json.load(f)
            for key, widget in self.entries.items():
                if (values.get(key)):
                    widget.SetValue(values[key])
            # self.Layout()
            if values.get('flag_MSR') and values.get('MSR'):
                self.msrPane.Collapse(False)
                self.msrRunBtn.Enable()
                self.msrPane.onLoad(values['MSR'])
                self.log.WriteText(f"MSR Loaded")
            if values.get('flag_KMC') and values.get('KMC'):
                self.kmcPane.Collapse(False)
                self.kmcRunBtn.Enable()
                self.kmcPane.OnLoad(values['KMC'])
                self.log.WriteText(f"KMC Loaded")
            self.OnInnerSizeChanged()
            self.log.WriteText(f"Inputs are loaded from {path}")
        dlg.Destroy()
    
    def OnClear(self):
        pass

    def OnRunMSR(self, event=None):
        if not self.msrOnoff.GetValue(): 
            return
        sj_start = time.time()
        self.__save()
        wulff = Wulff()

        flag, message = wulff.get_para(self.values)
        if flag:
            wulff.gen_coverage()
            flag, message = wulff.geometry()
            if flag:
                self.log.WriteText(f"MSR Job Completed.")
                self.log.WriteText(wulff.record_df)
                sj_elapsed = round(time.time() - sj_start, 4)
                q = 'MSR Job Completed. Total Cost About: ' + str(sj_elapsed) + ' Seconds\n'\
                    + 'Visulize the NanoParticles?'
                dlg = wx.MessageDialog(self, q, "Visualized?",
                                       style=wx.YES_NO|wx.ICON_INFORMATION)
                if dlg.ShowModal() == wx.ID_YES:
                    NP = NanoParticle(wulff.eles, wulff.positions, wulff.siteTypes)
                    self.particle = NP
                    self.topWin.VisualPanel.ChangeSelection(0)
                    self.topWin.glPanel.DrawMSR(NP)
            else:
                dlg = wx.MessageDialog(self, message, 
                                "Error when Running MSR", 
                                style=wx.OK|wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
        else:
            dlg = wx.MessageDialog(self, message, 
                                   "Error when loading inpus", 
                                   style=wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def OnRunKMC(self, event=None):
        if not self.kmcOnoff.GetValue():
            return
        sj_start = time.time()
        self.__save()
        self.log.WriteText("KMC Job Initiating...")
        if writeKmcInp(self.values):
            self.log.WriteText("KMC Job Started...")
            pwd0 = os.getcwd()
            os.chdir(os.path.join(pwd0, 'data'))
            out = subprocess.Popen("main.exe", shell=True, stdout=subprocess.PIPE)
            stdout, stderr = out.communicate()
            if not stderr:
                self.log.Write(stdout)
                sj_elapsed = round(time.time() - sj_start, 4)
                self.log.WriteText('KMC Job Completed. Total Cost About: ' + str(sj_elapsed) + ' Seconds')
                self.topWin.VisualPanel.ChangeSelection(1)
                DfTOF_site = self.topWin.pltPanle.post_kmc(self.kmcPane.products)
                if self.particle != None:
                    new_NP = self.particle
                else:
                    ele = self.values['Element']
                    new_NP = NanoParticle(ele, DfTOF_site[['x', 'y', 'z']], covTypes=DfTOF_site[['cov']])
                new_NP.addColorGCN(DfTOF_site[['gcn']])
                for pro in self.kmcPane.products:
                    key = pro.name
                    new_NP.addColorTOF(key, DfTOF_site[[key]])
                self.topWin.glPanel.DrawKMC(new_NP)
            else:
                self.log.WriteText('KMC Failed: Error when running.')
            os.chdir(pwd0)
        else:
            self.log.WriteText("KMC Failed: Error when loading inputs")

    def OnInnerSizeChanged(self):
        w,h = self.Box.GetMinSize()
        self.SetVirtualSize((w,h))
        self.Layout()


class MsrPanel(wx.CollapsiblePane):
    def __init__(self, parent : InputPanel):
        wx.CollapsiblePane.__init__(self, parent, label='MSR', name='msr')
        self.digitValidator = parent.digitValidator
        self.posDigitValidator = parent.posDigitValidator
        self.win = self.GetPane()
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.win.SetSizer(self.Box)
        self.parent = parent
        self.nGas = 3
        self.nFaces = 0
        self.initFace = 3
        self.faceRows = np.array([])
        # self.win.SetBackgroundColour('#f0f0f0')
        
        self.entries = {}
        self.values = {}

        self.__initrBox()
        self.Box.AddSpacer(8)
        self.__initGasesBox()
        self.Box.AddSpacer(8)
        self.__initFacesBox()

    def __initrBox(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        wgt = wx.TextCtrl(self.win, -1, size=(120, -1), style=wx.TE_CENTER)
        wgt.SetValidator(self.posDigitValidator)
        self.entries["Radius"] = wgt
        box.Add(wx.StaticText(self.win, -1, "Radius (\u00C5)"), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        box.AddSpacer(8)
        box.Add(wgt, 0, wx.ALIGN_CENTER|wx.ALL, 8)
        self.Box.Add(box)

    def __initGasesBox(self):
        gasBox = wx.StaticBox(self.win, -1, 'Gases Info')
        gasSizer = wx.StaticBoxSizer(gasBox, wx.VERTICAL)
        self.Box.Add(gasSizer, 0, wx.EXPAND|wx.ALL)
        gasGridS = wx.FlexGridSizer(4, 5, 8, 16)
        gasSizer.Add(gasGridS, 0, wx.EXPAND|wx.ALL)

        gasGridS.Add(wx.StaticText(self.win, label=''))
        gasGridS.Add(wx.StaticText(self.win, label='Name'), 0,  wx.ALIGN_CENTER_HORIZONTAL)
        gasGridS.Add(wx.StaticText(self.win, label='Partial Pressure (%)'), 0,  wx.ALIGN_CENTER_HORIZONTAL)
        gasGridS.Add(wx.StaticText(self.win, label='Standard Entropy (eV/K)'), 0,  wx.ALIGN_CENTER_HORIZONTAL)
        gasGridS.Add(wx.StaticText(self.win, label='Adsorption type'), 0,  wx.ALIGN_CENTER_HORIZONTAL)

        for i in range(1, self.nGas+1):
            gasGridS.Add(wx.StaticText(self.win, label=f" Gas{i} "), 
                         0,  wx.ALIGN_CENTER_HORIZONTAL)
            for param in ['name', 'pp', 'S']:
                ety = wx.TextCtrl(self.win, -1, size=(120, -1), style=wx.TE_CENTRE)
                self.entries[f"Gas{i}_{param}"] = ety
                gasGridS.Add(ety, 0, wx.EXPAND)
                if param != 'name':
                    ety.SetValidator(self.posDigitValidator)
            styles = ['Associative', 'Dissociative']
            combo = wx.ComboBox(self.win, -1, choices=styles, value=styles[0], 
                                size=(120, -1), style=wx.CB_READONLY)
            self.entries[f"Gas{i}_type"] = combo
            gasGridS.Add(combo, 0, wx.EXPAND)
        gasSizer.AddSpacer(4)

    def __initFacesBox(self):
        faceBox = wx.StaticBox(self.win, -1, 'Faces Info')
        faceSizer = wx.StaticBoxSizer(faceBox, wx.VERTICAL)
        self.Box.Add(faceSizer, 0, wx.EXPAND|wx.ALL)

        buttonSz = wx.BoxSizer(wx.HORIZONTAL)
        self.faceLabel = wx.StaticText(self.win, label=f"{self.nFaces}")
        addBtn = wx.Button(self.win, -1, 'Add')
        self.Bind(wx.EVT_BUTTON, self.__add, addBtn)
        delBtn = wx.Button(self.win, -1, 'Delete')
        self.Bind(wx.EVT_BUTTON, self.__del, delBtn)
        buttonSz.Add(wx.StaticText(self.win, label='Number of faces: '), 0, wx.ALIGN_CENTER|wx.ALL)
        buttonSz.Add(self.faceLabel, 0, wx.ALIGN_CENTER|wx.ALL)
        buttonSz.AddSpacer(16)
        buttonSz.Add(addBtn, 0, wx.ALIGN_CENTER|wx.ALL)
        buttonSz.AddSpacer(16)
        buttonSz.Add(delBtn, 0, wx.ALIGN_CENTER|wx.ALL)
        faceSizer.Add(buttonSz, 0, wx.EXPAND|wx.ALL, 4)

        self.gridSz = wx.GridBagSizer(vgap=8, hgap=16)
        self.gridSz.Add(wx.StaticText(self.win, label='index'), 
                        pos=(0, 0),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.gridSz.Add(wx.StaticText(self.win, label='Surface energy (eV/\u00C5²)'), 
                        pos=(0, 1),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.gridSz.Add(wx.StaticText(self.win, label='E_ads (eV)'), 
                        pos=(0, 2),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.gridSz.Add(wx.StaticText(self.win, label='S_ads (eV/K)'), 
                        pos=(0, 3),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.gridSz.Add(wx.StaticText(self.win, label='Lateral interaction (eV)'), 
                        pos=(0, 4),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        faceSizer.Add(self.gridSz, 0, wx.EXPAND|wx.ALL, 8)

        self.setFaces(self.initFace)

    def setFaces(self, nFaces: int):
        if nFaces < 1:
            return
        while(self.nFaces != nFaces):
            if (self.nFaces > nFaces):
                self.__delFace()
            else:
                self.__addFace()
        self.faceLabel.SetLabel(f"{self.nFaces}")
        for i in range(nFaces):
            if self.values.get(f"Face{i+1}"):
                subvalues = self.values[f"Face{i+1}"]
                self.faceRows[i].setValues(subvalues)

    def __addFace(self):
        self.nFaces += 1
        row = FaceRow(self, self.gridSz, self.nFaces)
        self.faceRows = np.append(self.faceRows, row)
    
    def __add(self, event):
        self.__addFace()
        self.faceLabel.SetLabel(f"{self.nFaces}")
        self.parent.OnInnerSizeChanged()
        
    def __delFace(self):
        if self.nFaces > 1:
            row, self.faceRows = self.faceRows[-1], self.faceRows[:-1]
            row.delete()
            self.nFaces -= 1
            return True
        return False

    def __del(self, event):
        if self.__delFace():
            self.faceLabel.SetLabel(f"{self.nFaces}")
            self.parent.OnInnerSizeChanged()

    def OnSave(self):
        for key, widget in self.entries.items():
            self.values[key] = widget.GetValue()
        self.values['nFaces'] = self.nFaces
        for i, row in enumerate(self.faceRows):
            self.values[f"Face{i+1}"] = row.getValues()
        return self.values

    def onLoad(self, values : dict):
        self.values = values
        for key, widget in self.entries.items():
            widget.SetValue(self.values.get(key, ''))
        if self.values.get('nFaces'):
            self.setFaces(nFaces=self.values['nFaces'])
            self.parent.OnInnerSizeChanged()


class FaceRow:
    def __init__(self, parent : MsrPanel, sizer : wx.GridBagSizer, idx : int):
        self.sizer = sizer
        self.idx = idx
        self.entries = []
        self.subentries = dict.fromkeys(["index", "gamma", "E_ads", "S_ads", "w"])
        self.subvalues = dict.fromkeys(["index", "gamma", "E_ads", "S_ads", "w"])

        self.parent = parent
        master = parent.win
        indexCtrl = wx.TextCtrl(master, -1, size=(120, -1), style=wx.TE_CENTRE, name='index')
        indexCtrl.SetValidator(parent.digitValidator)
        self.sizer.Add(indexCtrl, pos=(idx, 0),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.subentries['index'] = indexCtrl

        gammaCtrl = wx.TextCtrl(master, -1, size=(120, -1), style=wx.TE_CENTRE, name='index')
        gammaCtrl.SetValidator(parent.posDigitValidator)
        self.sizer.Add(gammaCtrl, pos=(idx, 1),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.subentries['gamma'] = gammaCtrl

        EadsBtn = wx.Button(master, -1, "Set", size=(120, -1))
        self.EadsWin = popupAdsInFace(parent)
        self.sizer.Add(EadsBtn, pos=(idx, 2),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.subentries['E_ads'] = self.EadsWin.entries
        EadsBtn.Bind(wx.EVT_BUTTON, lambda event: self.__onShowPopup(event, self.EadsWin))
        self.entries.append(EadsBtn)

        SadsBtn = wx.Button(master, -1, "Set", size=(120, -1))
        self.SadsWin = popupAdsInFace(parent)
        self.sizer.Add(SadsBtn, pos=(idx, 3),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.subentries['S_ads'] = self.SadsWin.entries
        SadsBtn.Bind(wx.EVT_BUTTON, lambda event: self.__onShowPopup(event, self.SadsWin))
        self.entries.append(SadsBtn)

        LIBtn = wx.Button(master, -1, "Set", size=(120, -1))
        self.LIWin = popupLiInFace(parent)
        self.sizer.Add(LIBtn, pos=(idx, 4),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.subentries['S_ads'] = self.LIWin.entries
        LIBtn.Bind(wx.EVT_BUTTON, lambda event: self.__onShowPopup(event, self.LIWin))
        self.entries.append(LIBtn)
    
    def __onShowPopup(self, event, win):
        btn = event.GetEventObject()
        pos = btn.ClientToScreen( (0,0) )
        sz =  btn.GetSize()
        
        win.Position(pos, (0, sz[1]))
        win.Popup(focus=win)

    def setValues(self, subvalues : dict):
        try:
            if subvalues.get('index'):
                self.subentries['index'].SetValue(f"{subvalues['index']}")
            if subvalues.get('gamma'):
                self.subentries['gamma'].SetValue(f"{subvalues['gamma']}")
            if subvalues.get('E_ads'):
                self.EadsWin.setValues(subvalues['E_ads'])
            if subvalues.get('S_ads'):
                self.SadsWin.setValues(subvalues['S_ads'])
            if subvalues.get('w'):
                self.LIWin.setValues(subvalues['w'])
                
        except KeyError as e:
            self.parent.parent.log.WriteText(e)

    def getValues(self):
        self.subvalues['index'] = self.subentries['index'].GetValue()
        self.subvalues['gamma'] = self.subentries['gamma'].GetValue()
        self.subvalues['E_ads'] = self.EadsWin.getValues()
        self.subvalues['S_ads'] = self.SadsWin.getValues()
        self.subvalues['w'] = self.LIWin.getValues()
        return self.subvalues

    def delete(self):
        # name as "delete" to avoid wrapped C/C++ object of type TextCtrl has been deleted error
        for widget in self.subentries.values():
            if widget:
                if isinstance(widget, np.ndarray) or isinstance(widget, list):
                    widget = np.array(widget)
                    for w in widget.flat:
                        w.Destroy()
                else:
                    widget.Destroy()

        for widget in self.entries:
            widget.Destroy()


class popupAdsInFace(wx.PopupTransientWindow):
    def __init__(self, parent : MsrPanel, style=wx.SIMPLE_BORDER|wx.PU_CONTAINS_CONTROLS, nGas=3):
        wx.PopupTransientWindow.__init__(self, parent, style)
        # self.values = np.zeros(nGas)
        self.SetBackgroundColour(POP_BG_COLOR)
        self.SetFont(GET_FONT())
        self.entries = []
        panel = wx.Panel(self)
        sz = wx.FlexGridSizer(nGas, 2, 0, 4)
        panel.SetSizer(sz)
        for i in range(nGas):
            sz.Add(wx.StaticText(panel, label=f"Gas{i+1}"), 0, wx.ALIGN_CENTER|wx.ALL, 6)
            ety = wx.TextCtrl(panel, -1, size=(80, -1), style=wx.TE_CENTER, name=f"{i}")
            ety.SetValue('0.00')
            ety.SetValidator(parent.digitValidator)
            sz.Add(ety, 0, wx.ALIGN_CENTER|wx.ALL, 6)
            self.entries.append(ety)
        sz.Fit(panel)
        sz.Fit(self)
        self.Layout()

    def setValues(self, values : list):
        for i, ety in enumerate(self.entries):
            ety.SetValue(f"{values[i]}")

    def getValues(self):
        values = []
        for ety in self.entries:
            values.append(ety.GetValue())
        return values


class popupLiInFace(wx.PopupTransientWindow):
    def __init__(self, parent : MsrPanel, style=wx.SIMPLE_BORDER|wx.PU_CONTAINS_CONTROLS, nGas=3):
        wx.PopupTransientWindow.__init__(self, parent, style)
        # self.values = np.zeros(nGas)
        self.SetBackgroundColour(POP_BG_COLOR)
        self.SetFont(GET_FONT())
        self.entries = []
        panel = wx.Panel(self)
        sz = wx.FlexGridSizer(nGas+1, nGas+1, 0, 4)
        panel.SetSizer(sz)
        sz.Add(wx.StaticText(panel, label=''))
        for i in range(nGas):
            sz.Add(wx.StaticText(panel, label=f"Gas{i+1}"), 0, wx.ALIGN_CENTER|wx.ALL, 6)
        for i in range(nGas):
            sz.Add(wx.StaticText(panel, label=f"Gas{i+1}"), 0, wx.ALIGN_CENTER|wx.ALL, 6)
            etys = []
            for j in range(nGas):
                ety = wx.TextCtrl(panel, -1, size=(80, -1), style=wx.TE_CENTER, name=f"{i}{j}")
                ety.SetValidator(parent.digitValidator)
                sz.Add(ety, 0, wx.ALIGN_CENTER|wx.ALL, 6)
                ety.SetValue('0.00')
                if j > i:
                    ety.SetEditable(False)
                    ety.SetBackgroundColour("#E0E0E0")
                else:
                    ety.Bind(wx.EVT_TEXT, self.__symText)
                etys.append(ety)
            self.entries.append(etys)
        sz.Fit(panel)
        sz.Fit(self)
        self.Layout()

    def __symText(self, event):
        obj = event.GetEventObject()
        i = int(obj.Name[0])
        j = int(obj.Name[1])
        if i != j:
            self.entries[j][i].SetValue(obj.GetValue())

    def setValues(self, values : list):
        for i, row in enumerate(self.entries):
            for j, ety in enumerate(row):
                ety.SetValue(f"{values[i][j]}")

    def getValues(self):
        values = []
        for row in self.entries:
            rowV = []
            for ety in row:
                rowV.append(ety.GetValue())
            values.append(rowV)
        return values


class KmcPanel(wx.CollapsiblePane):
    def __init__(self, parent : InputPanel):
        wx.CollapsiblePane.__init__(self, parent, label='KMC', name='kmc')
        self.parent = parent
        self.log = parent.log
        self.digitValidator = parent.digitValidator
        self.posDigitValidator = parent.posDigitValidator

        self.msrFlag = True
        self.iniFilePath = ""

        self.values = {}
        self.entries = {}
        self.nspecies = 0
        self.nproducts = 0
        self.nevents = 0
        self.species = np.array([])
        self.products = np.array([])

        # unlike species and products, events is not update chronically
        self.events = np.array([]) 

        # a bidirectional map between reactant and id
        self.id2reactantMap = bidict.bidict({0: "*"})   

        self.win = self.GetPane()
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.win.SetSizer(self.Box)
        
        nSpe = 1
        self.__initUI()
        self.__initSpecies()
        self.__initProducts()
        self.__initEvents()
        self.__initLi()
        self.spePane.setSpes(nSpe)
        self.liWin.setSpe(nSpe)
    
    def __initUI(self):
        self.padding = 4
        boxh1 = wx.BoxSizer(wx.HORIZONTAL)
        self.Box.Add(boxh1, 0, wx.EXPAND|wx.ALL)
        boxh1.AddSpacer(self.padding)
        boxh1.Add(wx.StaticText(self.win, label='Initial structure: '), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        iniStrList = ['MSR Structure', 'Read from file']
        radio0 = wx.RadioButton(self.win, -1, iniStrList[0], name="msr", style=wx.RB_GROUP)
        radio0.SetValue(0)
        radio1 = wx.RadioButton(self.win, -1, iniStrList[1], name="file")
        radio1.SetValue(0)
        self.iniStrCtrls = [radio0, radio1]
        boxh1.Add(radio0, 0, wx.ALIGN_CENTER|wx.ALL, 8)
        boxh1.Add(radio1, 0, wx.ALIGN_CENTER|wx.ALL, 8)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnGroupStrSelect, radio0)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnGroupStrSelect, radio1)

        boxh2 = wx.BoxSizer(wx.HORIZONTAL)
        self.Box.Add(boxh2, 0, wx.EXPAND|wx.ALL)
        boxh2.AddSpacer(self.padding)
        boxh2.Add(wx.StaticText(self.win, label='Total steps'), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        wgt = wx.TextCtrl(self.win, -1, size=(120, -1), style=wx.TE_CENTRE)
        wgt.SetValidator(self.posDigitValidator)
        boxh2.Add(wgt, 0, wx.EXPAND|wx.ALL, 8)
        self.entries['nLoop'] = wgt
        # boxh2.AddSpacer(8)
        boxh2.Add(wx.StaticText(self.win, label='Record interval'), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        wgt = wx.TextCtrl(self.win, -1, size=(120, -1), style=wx.TE_CENTRE)
        wgt.SetValidator(self.posDigitValidator)
        boxh2.Add(wgt, 0, wx.EXPAND|wx.ALL, 8)
        self.entries['record_int'] = wgt

    def __initSpecies(self):
        speBox = wx.StaticBox(self.win, -1, '')
        speSizer = wx.StaticBoxSizer(speBox, wx.VERTICAL)
        self.Box.Add(speSizer, 0, wx.EXPAND|wx.ALL)

        self.spePane = SpeciePane(self, self.win)
        speSizer.Add(self.spePane)

    def __initProducts(self):
        proBox = wx.StaticBox(self.win, -1, '')
        proSizer = wx.StaticBoxSizer(proBox, wx.VERTICAL)
        self.Box.Add(proSizer, 0, wx.EXPAND|wx.ALL)

        self.proPane = ProductPane(self, self.win)
        proSizer.Add(self.proPane)

    def __initEvents(self):
        evtBox = wx.StaticBox(self.win, -1, '')
        evtSizer = wx.StaticBoxSizer(evtBox, wx.VERTICAL)
        self.Box.Add(evtSizer, 0, wx.EXPAND|wx.ALL)

        self.evtPane = EventPane(self, self.win)
        evtSizer.Add(self.evtPane)

    def __initLi(self):
        liSz = wx.BoxSizer(wx.HORIZONTAL)
        self.Box.Add(liSz, 0, wx.EXPAND|wx.ALL, 4)
        liSz.AddSpacer(self.padding)
        liSz.Add(wx.StaticText(self.win, label='Lateral interacion (eV): '), 
                 0, wx.ALIGN_CENTER|wx.ALL)
        liBtn = wx.Button(self.win, -1, "Set")
        self.liWin = LiPane(self.win)
        liBtn.Bind(wx.EVT_BUTTON, lambda event: self.__onShowPopup(event, self.liWin))
        liSz.AddSpacer(8)
        liSz.Add(liBtn, 0, wx.ALIGN_CENTER|wx.ALL)

    def __onShowPopup(self, event, win):
        btn = event.GetEventObject()
        pos = btn.ClientToScreen( (0,0) )
        sz =  btn.GetSize()
        
        win.Position(pos, (0, sz[1]))
        win.Popup(focus=win)

    def updateIdMap_twosite(self, id, name):
        try:
            self.id2reactantMap[id] = f"{name}@i*"
            self.id2reactantMap[-id] = f"{name}@j*"
            for evtRow in np.append(self.evtPane.mobRows, self.evtPane.fixRows):
                evtRow.updateReactants()
        except bidict.ValueDuplicationError:
            self.log.WriteText("Please ensure the unique of name")
        print(self.id2reactantMap)

    def updateIdMap(self, id, name):
        if type(id) == int:
            name = name + "*"
        try:
            self.id2reactantMap[id] = name
            for evtRow in np.append(self.evtPane.mobRows, self.evtPane.fixRows):
                evtRow.updateReactants()
        except bidict.ValueDuplicationError:
            self.log.WriteText("Please ensure the unique of name")
        # print(self.id2reactantMap)
    
    def popIdMap_twosite(self, id):
        self.id2reactantMap.pop(id)
        self.id2reactantMap.pop(-id)
        for evtRow in np.append(self.evtPane.mobRows, self.evtPane.fixRows):
            evtRow.updateReactants()

    def popIdMap(self, id):
        self.id2reactantMap.pop(id)
        for evtRow in np.append(self.evtPane.mobRows, self.evtPane.fixRows):
            evtRow.updateReactants()
        # print(self.id2reactantMap)

    def OnSave(self):
        for key, widget in self.entries.items():
            self.values[key] = widget.GetValue()
        self.values['nspecies'] = self.nspecies
        self.values['nproducts'] = self.nproducts
        self.values['nevents'] = self.nevents
        self.values['nevents_mob'] = self.evtPane.getNmobE()
        for i, spe in enumerate(self.species):
            self.values[f"s{i+1}"] = json.dumps(spe, cls=Specie.Encoder)
        # initiate num_gen/consum and event_gen/consum of products
        for pro in self.products:
            pro.reset()
        self.events = self.evtPane.OnSave()
        for i, pro in enumerate(self.products):
            self.values[f"p{i+1}"] = json.dumps(pro, cls=Product.Encoder)
        for i, evt in enumerate(self.events):
            self.values[f"e{i+1}"] = json.dumps(evt, cls=Event.Encoder)
        self.values["li"] = self.liWin.getValues()
        return self.values

    def OnLoad(self, values : dict):
        self.values = values
        for key, widget in self.entries.items():
            widget.SetValue(self.values.get(key, ''))
        if self.values.get('nspecies'):
            self.spePane.setSpes(nSpe=self.values['nspecies'])
        if self.values.get('nproducts'):
            self.proPane.setPros(nPro=self.values['nproducts'])
        if self.values.get('nevents'):
            nEvt = self.values['nevents']
            nMob = self.values.get('nevents_mob', nEvt)
            self.evtPane.setEvts(nEvt, nMob)
        if self.values.get('li'):
            self.liWin.setValues(self.values['li'])

    def OnGroupStrSelect(self, event):
        radio_selected = event.GetEventObject()
        print('EvtRadioBox: %s' % radio_selected.Name)
        pass


class SpeciePane(wx.Panel):
    def __init__(self, master : KmcPanel, parent):
        wx.Panel.__init__(self, parent, name="spePane")
        # self.SetScrollRate(10, 10)
        self.master = master
        self.rows = np.array([])
        self._nSpes = 0

        mainBox = wx.BoxSizer(wx.VERTICAL) 
        self.SetSizer(mainBox)
        
        buttonSz = wx.BoxSizer(wx.HORIZONTAL)
        mainBox.Add(buttonSz, 0, wx.EXPAND|wx.ALL, 4)
        buttonSz.AddSpacer(self.master.padding)
        buttonSz.Add(wx.StaticText(self, label='Number of adsorbed species: '), 
                     0, wx.ALIGN_CENTER|wx.ALL)
        self.speLabel = wx.StaticText(self, label=f"{self._nSpes}")
        addBtn = wx.Button(self, -1, 'Add')
        self.Bind(wx.EVT_BUTTON, self.__add, addBtn)
        delBtn = wx.Button(self, -1, 'Delete')
        self.Bind(wx.EVT_BUTTON, self.__del, delBtn)
        buttonSz.Add(self.speLabel, 0, wx.ALIGN_CENTER|wx.ALL)
        buttonSz.AddSpacer(16)
        buttonSz.Add(addBtn, 0, wx.ALIGN_CENTER|wx.ALL)
        buttonSz.AddSpacer(16)
        buttonSz.Add(delBtn, 0, wx.ALIGN_CENTER|wx.ALL)

        self.box = wx.BoxSizer(wx.VERTICAL) # box to put SpeRows
        mainBox.Add(self.box, 0, wx.EXPAND|wx.ALL)

    def __addSpe(self):
        self.master.nspecies += 1
        self._nSpes += 1
        id = self._nSpes
        newSpe = Specie(f"Specie{id}")
        newRow = SpecieRow(self, id, newSpe)
        self.rows = np.append(self.rows, newRow)
        self.master.species = np.append(self.master.species, newSpe)
        self.master.updateIdMap(id, newSpe.getName()) ## idMap
        self.master.liWin.addSpe() ## li
        self.master.liWin.setLabel(id, newSpe.getName()) ## li
        self.box.Add(newRow, 0, wx.EXPAND|wx.ALL, 4)
    
    def __add(self, event):
        self.__addSpe()
        self.speLabel.SetLabel(f"{self._nSpes}")
        self.master.parent.OnInnerSizeChanged()

    def __delSpe(self):
        if self._nSpes > 1:
            id = self._nSpes
            self.master.liWin.delSpe()  ## li
            self.master.nspecies -= 1
            self._nSpes -= 1
            lastRow, self.rows = self.rows[-1], self.rows[:-1]
            lastSpe, self.master.species = self.master.species[-1], self.master.species[:-1]
            if lastSpe.is_twosite:
                self.master.popIdMap_twosite(id) ## idMap
            else:
                self.master.popIdMap(id) ## idMap
            lastRow.delete()
            del lastRow
            del lastSpe
            return True
        return False

    def __del(self, event):
        if self.__delSpe():
            self.speLabel.SetLabel(f"{self._nSpes}")
            # self.master.Layout()
            self.master.parent.OnInnerSizeChanged()
  
    def setSpes(self, nSpe : int):
        nSpe = int(nSpe)
        if nSpe < 1:
            return
        while (self._nSpes != nSpe):
            if (self._nSpes > nSpe):
                self.__delSpe()
            else:
                self.__addSpe()
        self.speLabel.SetLabel(f"{nSpe}")
        for i, row in enumerate(self.rows):
            if self.master.values.get(f"s{i+1}"):
                speDict = json.loads(self.master.values[f"s{i+1}"])
                speDict["default_name"] = f"Specie{i+1}"
                newSpe = json.loads(json.dumps(speDict), cls=Specie.Decoder)
                self.master.species[i] = newSpe
                row.setSpe(newSpe)
    

class SpecieRow(wx.Panel):
    def __init__(self, parent : SpeciePane, id : int, spe : Specie):
        wx.Panel.__init__(self, parent)
        self.master = parent.master
        self.id = id
        self.sepcie = spe
        self.digitValidator = parent.master.digitValidator
        self.posDigitValidator = parent.master.posDigitValidator

        self._btnDict = {}
        self._rowDict = dict(flag_ads=None, flag_des=None, flag_diff=None)
        self._evtDict = {}
        self._map = {"Adsorption": "flag_ads", 
                     "Desorption": "flag_des",
                     "Diffusion": "flag_diff"}

        self.subEntries = {}
        self.subBox = wx.GridBagSizer(vgap=4, hgap=16)
        self.SetSizer(self.subBox)
        self.__initUI()
        self.__SetValues()

    def __initUI(self):
        nameEty = wx.TextCtrl(self, -1, size=(100, -1), style=wx.TE_CENTER)
        nameEty.Bind(wx.EVT_TEXT, lambda event: self.onTextChange(event, self.sepcie, 'name'))
        self.subEntries["name"] = nameEty

        msg = "Turning on when specie occupies two adsorption sites.\n" \
            + "Adsorption, desorption and diffusion of two-site species are not allowed"
        siteOnOff = oob.OnOffButton(self, -1, "Two-site", initial=0, name="is_twosite")
        siteOnOff.SetBackgroundColour(BG_COLOR)
        siteOnOff.SetFont(GET_FONT())
        self.subEntries["is_twosite"] = siteOnOff
        staticInfoBmp = wx.StaticBitmap(self, -1, GET_INFO_BMP())
        staticInfoBmp.SetToolTip(msg)
        siteBtn = wx.Button(self, -1, "Set", size=(80, -1))
        self._btnDict["is_twosite"] = siteBtn

        adsOnoff = oob.OnOffButton(self, -1, "Adsorption", initial=0, name="flag_ads")
        adsOnoff.SetBackgroundColour(BG_COLOR)
        adsOnoff.SetFont(GET_FONT())
        self.subEntries["flag_ads"] = adsOnoff
        desOnoff = oob.OnOffButton(self, -1, "Desorption", initial=0, name="flag_des")
        desOnoff.SetBackgroundColour(BG_COLOR)
        desOnoff.SetFont(GET_FONT())
        self.subEntries["flag_des"] = desOnoff
        adsDesBtn = wx.Button(self, -1, "Set", size=(120, -1))
        self.adsDesWin = popupAdsDesInSpe(self)
        adsDesBtn.Bind(wx.EVT_BUTTON, lambda event: self.__onShowPopup(event, self.adsDesWin))
        self._btnDict["flag_ads"] = adsDesBtn
        self._btnDict["flag_des"] = adsDesBtn
        
        diffOnOff = oob.OnOffButton(self, -1, "Diffusion", initial=0, name="flag_diff")
        diffOnOff.SetBackgroundColour(BG_COLOR)
        diffOnOff.SetFont(GET_FONT())
        self.subEntries["flag_diff"] = diffOnOff
        diffBtn = wx.Button(self, -1, "Set", size=(80, -1))
        self._btnDict["flag_diff"] = diffBtn

        self.Bind(oob.EVT_ON_OFF, self.__SwOnOff)

        col = 0
        self.subBox.Add(nameEty, pos=(0, col), span=(2, 1), flag=wx.ALIGN_CENTER|wx.ALL)
        
        col += 1
        self.subBox.Add(wx.StaticText(self, label=""), pos=(0, col), span=(2, 1))

        col += 1
        siteBox = wx.BoxSizer(wx.HORIZONTAL)
        siteBox.Add(siteOnOff, 0)
        siteBox.Add(staticInfoBmp, 0, wx.ALIGN_CENTER)
        self.subBox.Add(siteBox, pos=(0, col), flag=wx.ALIGN_CENTER|wx.ALL)
        self.subBox.Add(siteBtn, pos=(1, col), flag=wx.ALIGN_CENTER|wx.ALL)

        col += 1
        self.subBox.Add(wx.StaticText(self, label=""), pos=(0, col), span=(2, 1))

        col += 1
        self.subBox.Add(adsOnoff, pos=(0, col), flag=wx.ALIGN_CENTER|wx.ALL)
        self.subBox.Add(desOnoff, pos=(0, col+1), flag=wx.ALIGN_CENTER|wx.ALL)
        self.subBox.Add(adsDesBtn, pos=(1, col), span=(1, 2), flag=wx.ALIGN_CENTER|wx.ALL)

        col += 2
        self.subBox.Add(wx.StaticText(self, label=""), pos=(0, col), span=(2, 1))

        col += 1
        self.subBox.Add(diffOnOff, pos=(0, col), flag=wx.ALIGN_CENTER|wx.ALL)
        self.subBox.Add(diffBtn, pos=(1, col), flag=wx.ALIGN_CENTER|wx.ALL)
    
    def __SwOnOff(self, event):
        obj = event.GetEventObject()
        name = obj.Name
        self.onTextChange(event, self.sepcie, name)
        if (name == "is_twosite"):
            self.__DisableEvtOnoff(obj.GetValue())
        else:
            self._btnDict[name].Enable(obj.GetValue())
            if obj.GetValue():
                evt = self._evtDict[name]
                self._rowDict[name] = self.master.evtPane.addFixEvt(evt, True)
            else:
                row = self._rowDict[name]
                if row:
                    self.master.evtPane.delFixEvt(row, True)
                    self._rowDict[name] = None

    def __onShowPopup(self, event, win):
        btn = event.GetEventObject()
        pos = btn.ClientToScreen( (0,0) )
        sz =  btn.GetSize()
        
        win.Position(pos, (0, sz[1]))
        win.Popup(focus=win)

    def __SetValues(self):
        spe = self.sepcie
        self.subEntries["name"].SetHint(spe.default_name)
        if spe.name:
            self.subEntries["name"].SetValue(spe.name)
            self.__SetEvts(spe.name)
        else:
            self.__SetEvts(f"spe{self.id}")
        self.subEntries["flag_ads"].SetValue(spe.flag_ads)
        self.subEntries["flag_des"].SetValue(spe.flag_des)
        self._btnDict["flag_ads"].Enable(spe.flag_ads and spe.flag_des)

        self.subEntries["flag_diff"].SetValue(spe.flag_diff)
        self._btnDict["flag_diff"].Enable(spe.flag_diff)

        self.subEntries["is_twosite"].SetValue(spe.is_twosite)
        self.subEntries["flag_diff"].Enable(not spe.is_twosite)
        self._btnDict["flag_diff"].Enable(not spe.is_twosite)
        if not spe.is_twosite:
            pass
        else:
            pass
        self.adsDesWin.setValues(spe.getAdsDesAttr())

    def __DisableEvtOnoff(self, flag : bool):
        keys = ["flag_ads", "flag_des", "flag_diff"]
        for key in keys:
            onoff = self.subEntries[key]
            btn = self._btnDict[key]
            row = self._rowDict[key]
            if flag:
                onoff.SetValue(0)
                onoff.Disable()
                btn.Disable()
                if row:
                    self.master.evtPane.delFixEvt(row)
                    self._rowDict["flag_diff"] = None
            else:
                onoff.Enable()

    def __SetEvts(self, name : str):
        self._evtDict["flag_ads"] = Event(
            name=f"{name}-ads", type="Adsorption", is_twosite=False, 
            cov_before=[0, 0], cov_after=[self.id, 0], 
            toggled=True, toggle_spe = self.id)
        self._evtDict["flag_des"] = Event(
            name=f"{name}-des", type="Desorption", is_twosite=False, 
            cov_before=[self.id, 0], cov_after=[0, 0], 
            toggled=True, toggle_spe=self.id)
        self._evtDict["flag_diff"] = Event(
            name=f"{name}-diff", type="Diffusion", is_twosite=True, 
            cov_before=[self.id, 0], cov_after=[0, self.id], 
            toggled=True, toggle_spe=self.id)
    
    def __ChangeEvtsName(self, name : str):
        for key in ["ads", "des", "diff"]:
            self._evtDict[f"flag_{key}"].name = f"{name}-{key}"
            row = self._rowDict[f"flag_{key}"]
            if row:
                row.updateName(f"{name}-{key}") 

    def onTextChange(self, event, instance:Specie, attr:str):
        value = event.GetEventObject().GetValue()
        setattr(instance, attr, value)
        if attr == "name":
            if instance.is_twosite:
                self.master.updateIdMap_twosite(self.id, instance.getName())
            else:
                self.master.updateIdMap(self.id, instance.getName()) ## idMap
            self.master.liWin.setLabel(self.id, instance.getName()) ## li
            self.__ChangeEvtsName(instance.getName())
        # print(instance)
    
    def bindEvt(self, evt, row):
        key = self._map.get(evt.type, None)
        if key:
            self._evtDict[key] = evt
            self._rowDict[key] = row

    def setSpe(self, spe : Specie):
        del self.sepcie
        self.sepcie = spe
        # self.master.updateIdMap(self.id, spe.getName())
        self.__SetValues()

    def delete(self):
        """ for widget in self.subEntries.values():
            widget.Destroy() """
        self.Destroy()


class popupAdsDesInSpe(wx.PopupTransientWindow):
    def __init__(self, parent : SpecieRow, style=wx.SIMPLE_BORDER|wx.PU_CONTAINS_CONTROLS):
        wx.PopupTransientWindow.__init__(self, parent, style)
        self.SetBackgroundColour(POP_BG_COLOR)
        self.SetFont(GET_FONT())
        self.keys = ["mass", "PP_ratio", "S_gas", "S_ads", "sticking"]
        self.entries = dict.fromkeys(self.keys)

        panel = wx.Panel(self)
        mainbox = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(mainbox)
        boxh1 = wx.BoxSizer(wx.HORIZONTAL)
        boxh2 = wx.BoxSizer(wx.HORIZONTAL)
        boxh3 = wx.BoxSizer(wx.HORIZONTAL)
        mainbox.Add(boxh1, 0, wx.EXPAND|wx.ALL)
        mainbox.Add(boxh2, 0, wx.EXPAND|wx.ALL)
        mainbox.Add(boxh3, 0, wx.EXPAND|wx.ALL)
        
        boxh1.Add(
            wx.StaticText(panel, label='Molecular mass'), 
            0, wx.ALIGN_CENTER|wx.ALL, 8
        )
        massEty = wx.TextCtrl(panel, -1, size=(100, -1), style=wx.TE_CENTER, name="mass")
        massEty.SetValidator(parent.posDigitValidator)
        massEty.Bind(wx.EVT_TEXT, lambda event: parent.onTextChange(event, parent.sepcie, 'mass'))
        self.entries['mass'] = massEty
        boxh1.Add(massEty, 0, wx.ALL, 8)
        boxh1.Add(
            wx.StaticText(panel, label='Pressure fracion (%)'), 
            0, wx.ALIGN_CENTER|wx.ALL, 8
        )
        ppEty = wx.TextCtrl(panel, -1, size=(100, -1), style=wx.TE_CENTER, name="PP_ratio")
        ppEty.SetValidator(parent.posDigitValidator)
        ppEty.Bind(wx.EVT_TEXT, lambda event: parent.onTextChange(event, parent.sepcie, 'PP_ratio'))
        self.entries['PP_ratio'] = ppEty
        boxh1.Add(ppEty, 0, wx.ALL, 8)

        boxh2.Add(
            wx.StaticText(panel, label='Entropy (eV/K) -- of adsorbed specie'), 
            0, wx.ALIGN_CENTER|wx.ALL, 8
        )
        SadsEty = wx.TextCtrl(panel, -1, size=(100, -1), style=wx.TE_CENTER, name="S_ads")
        SadsEty.SetValidator(parent.digitValidator)
        SadsEty.Bind(wx.EVT_TEXT, lambda event: parent.onTextChange(event, parent.sepcie, 'S_ads'))
        self.entries['S_ads'] = SadsEty
        boxh2.Add(SadsEty, 0, wx.ALL, 8)
        boxh2.Add(
            wx.StaticText(panel, label=' -- of standard gas-phase specie'), 
            0, wx.ALIGN_CENTER|wx.ALL, 8
        )
        SgasEty = wx.TextCtrl(panel, -1, size=(100, -1), style=wx.TE_CENTER, name="S_gas")
        SgasEty.SetValidator(parent.digitValidator)
        SgasEty.Bind(wx.EVT_TEXT, lambda event: parent.onTextChange(event, parent.sepcie, 'S_gas'))
        self.entries['S_gas'] = SgasEty
        boxh2.Add(SgasEty, 0, wx.ALL, 8)

        boxh3.Add(
            wx.StaticText(panel, label='Sticking coefficient (eV) -- on facets'), 
            0, wx.ALIGN_CENTER|wx.ALL, 8
        )
        S0FaceEty = wx.TextCtrl(panel, -1, size=(100, -1), style=wx.TE_CENTER, name="sticking0")
        S0FaceEty.SetValidator(parent.posDigitValidator)
        S0FaceEty.Bind(wx.EVT_TEXT, lambda event: parent.onTextChange(event, parent.sepcie, 'sticking0'))
        boxh3.Add(S0FaceEty, 0, wx.ALL, 8)
        boxh3.Add(
            wx.StaticText(panel, label=' -- on edges and corners'), 
            0, wx.ALIGN_CENTER|wx.ALL, 8
        )
        S0CeEty = wx.TextCtrl(panel, -1, size=(100, -1), style=wx.TE_CENTER, name="sticking1")
        S0CeEty.SetValidator(parent.posDigitValidator)
        S0CeEty.Bind(wx.EVT_TEXT, lambda event: parent.onTextChange(event, parent.sepcie, 'sticking1'))
        self.entries['sticking'] = [S0FaceEty, S0CeEty]
        boxh3.Add(S0CeEty, 0, wx.ALL, 8)

        mainbox.Fit(panel)
        mainbox.Fit(self)
        self.Layout()

    def setValues(self, values):
        # print(values)
        for key, widget in self.entries.items():
            value = values.get(key)
            if value == None : return
            if key == "sticking":
                widget[0].SetValue(f"{value[0]}")
                widget[1].SetValue(f"{value[1]}")
            else:
                widget.SetValue(f"{value}")


class LiPane(wx.PopupTransientWindow):
    def __init__(self, parent, style=wx.SIMPLE_BORDER|wx.PU_CONTAINS_CONTROLS):
        wx.PopupTransientWindow.__init__(self, parent, style)
        self.SetBackgroundColour(POP_BG_COLOR)
        self.SetFont(GET_FONT())
        self._nSpes = 0
        self.labels = []
        self.entries = []
        self.Sizer = wx.GridBagSizer(0, 6)
        self.SetSizerAndFit(self.Sizer)

    def __Label(self, label):
        return wx.StaticText(self, label=label)
    
    def __Text(self, row, col):
        return wx.TextCtrl(self, -1, size=(80, -1), style=wx.TE_CENTER, name=f"{row},{col}")
    
    def __OnText(self, event):
        obj = event.GetEventObject()
        labels = obj.Name.split(',')
        i = int(labels[0])
        j = int(labels[1])
        if i > j:
            layer = i-1
            n = len(self.entries[layer])
            self.entries[layer][j-1+(n-1)//2].SetValue(obj.GetValue())

    def addSpe(self):
        self._nSpes += 1
        n = self._nSpes
        labelRow = self.__Label(f"Specie{n}")
        labelCol = self.__Label(f"Specie{n}")
        self.Sizer.Add(labelRow, pos=(n, 0), flag=wx.ALIGN_CENTER|wx.ALL, border=4)
        self.Sizer.Add(labelCol, pos=(0, n), flag=wx.ALIGN_CENTER|wx.ALL, border=4)
        self.labels.append((labelRow, labelCol))
        newLayer = []
        for i in range(n-1):
            text = self.__Text(n, i+1)
            self.Sizer.Add(text, pos=(n, i+1), flag=wx.ALIGN_CENTER|wx.ALL, border=4)
            newLayer.append(text)
            text.Bind(wx.EVT_TEXT, self.__OnText)
        for j in range(n-1):
            text = self.__Text(j+1, n)
            self.Sizer.Add(text, pos=(j+1, n), flag=wx.ALIGN_CENTER|wx.ALL, border=4)
            text.SetEditable(False)
            text.SetBackgroundColour("#E0E0E0")
            newLayer.append(text)
        text = self.__Text(n, n)
        self.Sizer.Add(text, pos=(n, n), flag=wx.ALIGN_CENTER|wx.ALL, border=4)
        newLayer.append(text)
        self.entries.append(newLayer)
        self.Sizer.Fit(self)
        self.Layout()

    def delSpe(self):
        if self._nSpes > 0:
            lastLayer = self.entries.pop()
            for text in lastLayer:
                self.Sizer.Detach(text)
                text.Destroy()
            (label1, label2) = self.labels.pop()
            label1.Destroy()
            label2.Destroy()
            self._nSpes -= 1
            self.Sizer.Fit(self)
            self.Layout()

    def setSpe(self, nSpe : int, labels=None, values=None):
        if nSpe < 0:
            return
        while (self._nSpes != nSpe):
            if (self._nSpes > nSpe):
                self.delSpe()
            else:
                self.addSpe()
        if labels:
            self.setLabels(labels)
        if values:
            self.setValues(values)
        self.Sizer.Fit(self)
        self.Layout()     

    def setLabel(self, id, name):
        (row, col) = self.labels[id - 1]
        row.SetLabel(name)
        col.SetLabel(name)
        self.Layout()

    def setLabels(self, namelist):
        if len(namelist) <= self._nSpes:
            for i, name in namelist:
                self.setLabel(i+1, name)

    def setValues(self, li):
        if len(li) != self._nSpes: return False
        for layer in self.entries:
            for ety in layer:
                labels = ety.Name.split(',')
                i = int(labels[0]) - 1
                j = int(labels[1]) - 1
                ety.SetValue(f"{li[i][j]}")
        return True

    def getValues(self):
        values = np.zeros((self._nSpes, self._nSpes))
        for layer in self.entries:
            for ety in layer:
                labels = ety.Name.split(',')
                i = int(labels[0]) - 1
                j = int(labels[1]) - 1
                values[i][j] = ety.GetValue()
        return values.tolist()


class ProductPane(wx.Panel):
    def __init__(self, master : KmcPanel, parent):
        wx.Panel.__init__(self, parent, name="proPane")
        self.master = master
        self.Texts = np.array([])
        self._npros = 0
        self._maxCol = 6

        mainBox = wx.BoxSizer(wx.VERTICAL) 
        self.SetSizer(mainBox)

        buttonSz = wx.BoxSizer(wx.HORIZONTAL)
        mainBox.Add(buttonSz, 0, wx.EXPAND|wx.ALL, 4)
        buttonSz.AddSpacer(self.master.padding)
        buttonSz.Add(wx.StaticText(self, label='Number of products: '), 
                     0, wx.ALIGN_CENTER|wx.ALL)
        self.proLabel = wx.StaticText(self, label=f"{self.master.nproducts}")
        addBtn = wx.Button(self, -1, 'Add')
        self.Bind(wx.EVT_BUTTON, self.__add, addBtn)
        delBtn = wx.Button(self, -1, 'Delete')
        self.Bind(wx.EVT_BUTTON, self.__del, delBtn)
        buttonSz.Add(self.proLabel, 0, wx.ALIGN_CENTER|wx.ALL)
        buttonSz.AddSpacer(16)
        buttonSz.Add(addBtn, 0, wx.ALIGN_CENTER|wx.ALL)
        buttonSz.AddSpacer(16)
        buttonSz.Add(delBtn, 0, wx.ALIGN_CENTER|wx.ALL)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(self.master.padding)
        # box.Add(wx.StaticText(self, -1, "Name"), flag=wx.ALIGN_TOP, border=4)
        # box.AddSpacer(2*self.master.padding)
        self.box = wx.GridSizer(6, 8, 16)
        box.Add(self.box, 0, wx.EXPAND|wx.ALIGN_TOP)
        mainBox.Add(box, 0, wx.EXPAND|wx.ALL, 4)
    
    def __addPro(self):
        self.master.nproducts += 1
        self._npros += 1
        id = self._npros
        newPro = Product(f"Product{id}")
        newText = wx.TextCtrl(self, -1, style=wx.TE_CENTER)
        newText.SetHint(f"Product{id}")
        self.box.Add(newText, flag=wx.ALIGN_CENTER)
        self.Layout()
        newText.Bind(wx.EVT_TEXT, lambda event: self.__onNameChange(event, newPro, id))
        self.Texts = np.append(self.Texts, newText)
        self.master.products = np.append(self.master.products, newPro)
        self.master.updateIdMap(f"p{id}", newPro.getName())

    def __onNameChange(self, event, instance:Product, id:int):
        value = event.GetEventObject().GetValue()
        setattr(instance, "name", value)
        self.master.updateIdMap(f"p{id}", instance.getName())

    def __add(self, event):
        self.__addPro()
        self.proLabel.SetLabel(f"{self._npros}")
        self.master.parent.OnInnerSizeChanged()

    def __delPro(self):
        id = self._npros
        lastText, self.Texts = self.Texts[-1], self.Texts[:-1]
        lastPro, self.master.products = self.master.products[-1], self.master.products[:-1]
        lastText.Destroy()
        self.Layout()
        del lastPro
        self.master.popIdMap(f"p{id}")
        self.master.nproducts -= 1
        self._npros -= 1

    def __del(self, event):
        if self._npros > 0:
            self.__delPro()
            self.proLabel.SetLabel(f"{self._npros}")
            self.master.parent.OnInnerSizeChanged()

    def setPros(self, nPro : int):
        nPro = int(nPro)
        if nPro < 0:
            return
        while (self._npros != nPro):
            if (self._npros > nPro):
                self.__delPro()
            else:
                self.__addPro()
        self.proLabel.SetLabel(f"{nPro}")
        for i, text in enumerate(self.Texts):
            if self.master.values.get(f"p{i+1}"):
                proDict = json.loads(self.master.values[f"p{i+1}"])
                proDict["default_name"] = f"Product{i+1}"
                newPro = json.loads(json.dumps(proDict), cls=Product.Decoder)
                self.master.products[i] = newPro
                text.SetValue(newPro.getName())

    def update(self):
        self.master.parent.OnInnerSizeChanged()

class EventPane(wx.Panel):
    def __init__(self, master : KmcPanel, parent):
        wx.Panel.__init__(self, parent, name="evtPane")
        self.master = master
        self.log = master.log
        self.fixRows = np.array([])
        self.mobRows = np.array([])
        self._nMobEvnets = 0

        self.mainBox = wx.BoxSizer(wx.VERTICAL) 
        self.SetSizer(self.mainBox)

        buttonSz = wx.BoxSizer(wx.HORIZONTAL)
        self.mainBox.Add(buttonSz, 0, wx.EXPAND|wx.ALL, 4)
        buttonSz.AddSpacer(self.master.padding)
        buttonSz.Add(wx.StaticText(self, label='Number of events: '), 
                     0, wx.ALIGN_CENTER|wx.ALL)
        self.evtLabel = wx.StaticText(self, label=f"{self.master.nevents}")
        addBtn = wx.Button(self, -1, 'Add')
        self.Bind(wx.EVT_BUTTON, self.__add, addBtn)
        delBtn = wx.Button(self, -1, 'Delete')
        self.Bind(wx.EVT_BUTTON, self.__del, delBtn)
        buttonSz.Add(self.evtLabel, 0, wx.ALIGN_CENTER|wx.ALL)
        buttonSz.AddSpacer(16)
        buttonSz.Add(addBtn, 0, wx.ALIGN_CENTER|wx.ALL)
        buttonSz.AddSpacer(16)
        buttonSz.Add(delBtn, 0, wx.ALIGN_CENTER|wx.ALL)

        self.__initlabel()
        self.fixEvtBox = wx.BoxSizer(wx.VERTICAL)
        self.mobEvtBox = wx.BoxSizer(wx.VERTICAL)
        self.mainBox.Add(self.fixEvtBox, 0, wx.EXPAND|wx.ALL)
        self.mainBox.Add(self.mobEvtBox, 0, wx.EXPAND|wx.ALL)
    
    def __initlabel(self):
        self.padding = 12
        self.width = 90
        box = wx.BoxSizer(wx.HORIZONTAL)
        nameText = wx.StaticText(self, label="Name", size=(100, -1), style=wx.ALIGN_CENTER|wx.ALL)
        box.Add(nameText, 0, 4)

        box.AddSpacer(self.padding)
        sitePane = wx.Panel(self, size=(85, -1))
        siteBox = wx.BoxSizer(wx.HORIZONTAL)
        sitePane.SetSizer(siteBox)
        siteText = wx.StaticText(sitePane, label="Two-Site", style=wx.ALIGN_CENTER|wx.ALL)
        msg = "Turning on when event involves two sites (denoted as i and j)."
        staticInfoBmp = wx.StaticBitmap(sitePane, -1, GET_INFO_BMP())
        staticInfoBmp.SetToolTip(msg)
        siteBox.AddSpacer(10)
        siteBox.Add(siteText, 0, wx.ALIGN_CENTER)
        siteBox.AddSpacer(4)
        siteBox.Add(staticInfoBmp, 0, wx.ALIGN_CENTER)
        box.Add(sitePane, 0, 4)

        box.AddSpacer(self.padding)
        text = wx.StaticText(self, label="Type", size=(100, -1), style=wx.ALIGN_CENTER|wx.ALL)
        box.Add(text, 0, 4)
        
        box.AddSpacer(self.padding)
        subpane = wx.Panel(self, size=(self.width, -1))
        subbox = wx.BoxSizer(wx.HORIZONTAL)
        subpane.SetSizer(subbox)
        subbox.AddSpacer(int(self.width/2-16))
        text = wx.StaticText(subpane, label="R@i", style=wx.ALIGN_CENTER|wx.ALL)
        msg = "Reactant on i site \nR@i + R@j \u2192 P@i + P@j"
        staticInfoBmp = wx.StaticBitmap(subpane, -1, GET_INFO_BMP())
        staticInfoBmp.SetToolTip(msg)
        subbox.Add(text, 0, wx.ALIGN_CENTER|wx.ALL)
        subbox.AddSpacer(4)
        subbox.Add(staticInfoBmp, 0, wx.ALIGN_CENTER)
        box.Add(subpane, 0, 4)
        
        box.AddSpacer(self.padding)
        text = wx.StaticText(self, label="R@j", size=(self.width, -1), style=wx.ALIGN_CENTER|wx.ALL)
        box.Add(text, 0, 4)
        
        box.AddSpacer(self.padding)
        subpane = wx.Panel(self, size=(self.width, -1))
        subbox = wx.BoxSizer(wx.HORIZONTAL)
        subpane.SetSizer(subbox)
        subbox.AddSpacer(int(self.width/2-16))
        text = wx.StaticText(subpane, label="P@i", style=wx.ALIGN_CENTER|wx.ALL)
        msg = "Product on i site \nR@i + R@j \u2192 P@i + P@j"
        staticInfoBmp = wx.StaticBitmap(subpane, -1, GET_INFO_BMP())
        staticInfoBmp.SetToolTip(msg)
        subbox.Add(text, 0, wx.ALIGN_CENTER|wx.ALL)
        subbox.AddSpacer(4)
        subbox.Add(staticInfoBmp, 0, wx.ALIGN_CENTER)
        box.Add(subpane, 0, 4)
        
        box.AddSpacer(self.padding)
        text = wx.StaticText(self, label="P@j", size=(self.width, -1), style=wx.ALIGN_CENTER|wx.ALL)
        box.Add(text, 0, 4)

        box.AddSpacer(self.padding)
        subpane = wx.Panel(self, size=(110, -1))
        subbox = wx.BoxSizer(wx.HORIZONTAL)
        subpane.SetSizer(subbox)
        text = wx.StaticText(subpane, label="BEP relation", style=wx.ALIGN_CENTER|wx.ALL)
        msg = "pass"
        staticInfoBmp = wx.StaticBitmap(subpane, -1, GET_INFO_BMP())
        staticInfoBmp.SetToolTip(msg)
        subbox.Add(text, 0, wx.ALIGN_CENTER|wx.ALL)
        subbox.AddSpacer(4)
        subbox.Add(staticInfoBmp, 0, wx.ALIGN_CENTER)
        box.Add(subpane, 0, 4)

        self.mainBox.Add(box)

    def __addEvt(self, box, newEvt=None):
        self.master.nevents += 1
        if not newEvt:
            newEvt = Event()
        newRow = EventRow(self, newEvt)
        box.Add(newRow, 0, wx.EXPAND|wx.ALL, 4)
        return newRow

    def __add(self, event):
        newRow = self.__addEvt(self.mobEvtBox)
        self.mobRows = np.append(self.mobRows, newRow)
        self._nMobEvnets += 1
        self.__refersh()
        
    def __delEvt(self, type):
        self.master.nevents -= 1
        if type: # mobRow
            lastRow, self.mobRows = self.mobRows[-1], self.mobRows[:-1]
        else: # fixRow
            lastRow, self.fixRows = self.fixRows[-1], self.fixRows[:-1]
        lastRow.delete()
        del lastRow

    def __del(self, event):
        if self._nMobEvnets > 0:
            self._nMobEvnets -= 1
            self.__delEvt(1)
            self.__refersh()
        
    def __refersh(self):
        self.evtLabel.SetLabel(f"{self.master.nevents}")
        self.master.parent.OnInnerSizeChanged()
    
    def addFixEvt(self, evt, refresh = False):
        # create by toggle in specieRow
        newRow = self.__addEvt(self.fixEvtBox, evt)
        self.fixRows = np.append(self.fixRows, newRow)
        newRow.SetWindowStyle(wx.BORDER_SUNKEN)
        newRow.setFix()
        if refresh:
            self.__refersh()
        return newRow
    
    def delFixEvt(self, row, refresh = False):
        # create by toggle in specieRow
        self.fixRows = self.fixRows[self.fixRows != row]
        row.delete()
        self.master.nevents -= 1
        if refresh:
            self.__refersh()

    def setEvts(self, nEvt : int, nMobE = 0):
        nMobE = int(nMobE)
        nEvt = int(nEvt)
        if (nMobE < 0 or nEvt < 1 or nEvt < nMobE):
            self.log.WriteText("Warning: error happens when loading events, please check 'nevnets'/'nevent_mob")
            return
        while (self._nMobEvnets != nMobE):
            if (self._nMobEvnets > nMobE):
                self.__delEvt(1)
                self._nMobEvnets -= 1
            else:
                newRow = self.__addEvt(self.mobEvtBox)
                self.mobRows = np.append(self.mobRows, newRow)
                self._nMobEvnets += 1
        for row in self.fixRows:
            row.delete()
            self.master.nevents -= 1
        self.fixRows = np.array([])
        n = 0
        for i in range(nEvt):
            if self.master.values.get(f"e{i+1}"):
                newEvt = json.loads(self.master.values[f"e{i+1}"], cls=Event.Decoder)
                if newEvt.toggled:
                    if newEvt.toggle_spe:
                        newRow = self.addFixEvt(newEvt, True)
                        self.master.spePane.rows[newEvt.toggle_spe - 1].bindEvt(newEvt, newRow)
                else:
                    self.mobRows[n].setEvt(newEvt)
                    n += 1
                    if n > self._nMobEvnets:
                        self.log.WriteText("Warning: error happens when loading events, please check the 'toggled' value of events")
        self.evtLabel.SetLabel(f"{self.master.nevents}")

    def __updatePro(self, id, cov_before, cov_after):
        for cov in cov_before:
            if type(cov) == str:
                pro = self.master.products[int(cov[1:]) - 1]
                pro.num_consum += 1
                pro.event_consum.append(id)
        for cov in cov_after:
            if type(cov) == str:
                pro = self.master.products[int(cov[1:]) - 1]
                pro.num_gen += 1
                pro.event_gen.append(id)

    def OnSave(self):
        evtList = []
        id = 1
        for row in self.fixRows:
            evt = row.event
            evtList.append(evt)
            self.__updatePro(id, evt.cov_before, evt.cov_after)
            id += 1
        for row in self.mobRows:
            evt = row.event
            evtList.append(evt)
            self.__updatePro(id, evt.cov_before, evt.cov_after)
            id += 1
        return evtList

    def getNmobE(self):
        return self._nMobEvnets

class EventRow(wx.Panel):
    def __init__(self, parent : EventPane, evt : Event):
        wx.Panel.__init__(self, parent)
        self.master = parent.master
        self.padding = parent.padding
        self.width = parent.width
        self.event = evt
        self.digitValidator = parent.master.digitValidator
        self.posDigitValidator = parent.master.posDigitValidator

        self._destroyed = False
        self._types = ["Adsorption", "Desorption", 
                       "Diffusion", "Reaction"]
        self._reactants = list(self.master.id2reactantMap.values())
        self.subEntries = dict.fromkeys(
            ["name", "is_twosite", "type", "cov_before", "cov_after"])
        self.subBox = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.subBox)
        self.__initUI()
        self.__SetValues()

    def __initUI(self):
        nameEty = wx.TextCtrl(self, -1, size=(100, -1), style=wx.TE_CENTER)
        nameEty.Bind(wx.EVT_TEXT, lambda event: self.onTextChange(event, self.event, 'name'))
        self.subEntries["name"] = nameEty

        sitePane = wx.Panel(self, size=(85, -1))
        siteBox = wx.BoxSizer(wx.HORIZONTAL)
        sitePane.SetSizer(siteBox)
        siteOnOff = oob.OnOffButton(sitePane, -1, "", initial=0, name="is_twosite")
        siteOnOff.SetBackgroundColour(BG_COLOR)
        siteOnOff.SetFont(GET_FONT())
        siteOnOff.Bind(oob.EVT_ON_OFF, self.__SwOnOff)
        self.subEntries["is_twosite"] = siteOnOff
        siteBox.AddSpacer(18)
        siteBox.Add(siteOnOff, 0, wx.ALIGN_CENTER|wx.ALL)

        typeCombo = wx.ComboBox(
            self, -1, choices=self._types, value=self._types[-1],
            size=(100, -1), style=wx.CB_READONLY, name="type")
        typeCombo.Bind(wx.EVT_COMBOBOX, self.__OnType)
        self.subEntries["type"] = typeCombo

        RiCombo = wx.ComboBox(
            self, -1, choices=self._reactants, value=self._reactants[0],
            size=(self.width, -1), style=wx.CB_READONLY, name="R0")
        RiCombo.Bind(wx.EVT_COMBOBOX, self.__OnReactant)
        RjCombo = wx.ComboBox(
            self, -1, choices=self._reactants, value=self._reactants[0],
            size=(self.width, -1), style=wx.CB_READONLY, name="R1")
        RjCombo.Bind(wx.EVT_COMBOBOX, self.__OnReactant)
        self.subEntries["cov_before"] = [RiCombo, RjCombo]
        
        PiCombo = wx.ComboBox(
            self, -1, choices=self._reactants, value=self._reactants[0],
            size=(self.width, -1), style=wx.CB_READONLY, name="P0")
        PiCombo.Bind(wx.EVT_COMBOBOX, self.__OnReactant)
        PjCombo = wx.ComboBox(
            self, -1, choices=self._reactants, value=self._reactants[0],
            size=(self.width, -1), style=wx.CB_READONLY, name="P1")
        PjCombo.Bind(wx.EVT_COMBOBOX, self.__OnReactant)
        self.subEntries["cov_after"] = [PiCombo, PjCombo]

        subpane = wx.Panel(self, size=(110, -1))
        subbox = wx.BoxSizer(wx.HORIZONTAL)
        subpane.SetSizer(subbox)
        self.BEPrBtn = wx.Button(subpane, -1, 'Set')
        self.PopWin = self.__CreatePopWin()
        self.BEPrBtn.Bind(wx.EVT_BUTTON, lambda event: self.__onShowPopup(event, self.PopWin))
        subbox.Add(self.BEPrBtn, 0)
        
        self.subBox.Add(nameEty, 0, wx.ALIGN_CENTER, 4)
        self.subBox.AddSpacer(self.padding)
        self.subBox.Add(sitePane, 0, wx.ALIGN_CENTER, 4)
        self.subBox.AddSpacer(self.padding)
        self.subBox.Add(typeCombo, 0, wx.ALIGN_CENTER, 4)
        self.subBox.AddSpacer(self.padding)
        self.subBox.Add(RiCombo, 0, wx.ALIGN_CENTER, 4)
        self.subBox.AddSpacer(self.padding)
        self.subBox.Add(RjCombo, 0, wx.ALIGN_CENTER, 4)
        self.subBox.AddSpacer(self.padding)
        self.subBox.Add(PiCombo, 0, wx.ALIGN_CENTER, 4)
        self.subBox.AddSpacer(self.padding)
        self.subBox.Add(PjCombo, 0, wx.ALIGN_CENTER, 4)
        self.subBox.AddSpacer(self.padding)
        self.subBox.Add(subpane, 0, wx.ALIGN_CENTER, 4)
        pass
    
    def __CreatePopWin(self):
        popWin = wx.PopupTransientWindow(
            self, flags=wx.SIMPLE_BORDER|wx.PU_CONTAINS_CONTROLS)
        popWin.SetBackgroundColour(POP_BG_COLOR)
        popWin.SetFont(GET_FONT())
        
        popBox = wx.BoxSizer(wx.VERTICAL)
        popWin.SetSizer(popBox)

        popBox.Add(wx.StaticText(popWin, -1, "Ea = k\u0394E + b"),
                   0, wx.ALIGN_CENTER|wx.ALL, 6)

        popBox.Fit(popWin)
        popWin.Layout()
        pass

        return popWin

    def __onShowPopup(self, event, win):
        btn = event.GetEventObject()
        pos = btn.ClientToScreen( (0,0) )
        sz =  btn.GetSize()
        
        win.Position(pos, (0, sz[1]))
        win.Popup(focus=win)

    def __OnType(self, event):
        obj = event.GetEventObject()
        name = obj.Name
        self.onTextChange(event, self.event, name)
        pass

    def __OnReactant(self, event):
        obj = event.GetEventObject()
        name = obj.Name
        value = self.master.id2reactantMap.inverse[obj.GetValue()]
        self.onTextChange(event, self.event, name, value)

    def __SwOnOff(self, event):
        obj = event.GetEventObject()
        name = obj.Name
        self.onTextChange(event, self.event, name)
        if name == "is_twosite":
            self.__enableRecj(obj.GetValue())

    def __enableRecj(self, flag):
        self.subEntries["cov_before"][1].Enable(flag)
        self.subEntries["cov_after"][1].Enable(flag)
            
    def __SetValues(self):
        evt = self.event
        # print(evt)
        for key, wgt in self.subEntries.items():
            value = getattr(evt, key)
            if key in ["cov_before", "cov_after"]:
                wgt[0].SetValue(self.master.id2reactantMap[value[0]])
                wgt[1].SetValue(self.master.id2reactantMap[value[1]])
            else:
                wgt.SetValue(value)
        self.__enableRecj(evt.is_twosite)

    def onTextChange(self, event, instance:Event, attr:str, value=None):
        if value == None:
            value = event.GetEventObject().GetValue()
        setattr(instance, attr, value)

    def updateReactants(self):
        self._reactants = list(self.master.id2reactantMap.values())
        for key in ["cov_before", "cov_after"]:
            combos = self.subEntries[key]
            values = getattr(self.event, key)
            for i in [0, 1]:
                combos[i].Set(self._reactants)
                name = self.master.id2reactantMap.get(values[i], "*")
                combos[i].SetValue(name)

    def updateName(self, name):
        self.event.name = name
        self.subEntries["name"].SetValue(name)

    def setEvt(self, evt):
        del self.event
        self.event = evt
        self.__SetValues()

    def setFix(self):
        self.subEntries["type"].Disable()

    def delete(self):
        if not self._destroyed:
            self.Destroy()
            self._destroyed = True


if __name__ == '__main__':
    class MyApp(wx.App):
        """
        TextCtrlWithImage Application.
        """
        def OnInit(self):
            """
            Create the TextCtrlWithImage application.
            """
            
            frame = wx.Frame(None, title="test", size=(800, 600))
            frame.SetBackgroundColour(BG_COLOR)
            panel = InputPanel(frame, None)
            panel.msrPane.Collapse(True)
            panel.msrOnoff.SetValue(0)
            panel.kmcPane.Collapse(False)
            panel.kmcOnoff.SetValue(1)
            frame.Show(True)
            
            return True
        
    app = MyApp(redirect=False)
    app.MainLoop()