"""
@author: yinglei
"""

import wx
import json
import time
import bidict
import numpy as np

try:
    from utils.msr import Wulff
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
    INFO_IMG = wx.Image("assets/info.png", wx.BITMAP_TYPE_PNG)
    INFO_IMG.Rescale(16, 16)
    INFO_BMP = wx.Bitmap(INFO_IMG)
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

        self.entries = {}
        self.values = {}
        self.__InitCommon()
        self.__InitOnoff()
        self.__InitMSR()
        self.__InitKMC()
    
    def __InitCommon(self):
        # dict-key, unit, type, combolist
        items = [("Element", '', 'Entry', ''),
                  ("Lattice constant", '(\u00C5)', 'Entry', 'POS_NUM_ONLY'),
                  ("Crystal structure", '', 'Combobox', ('FCC', 'BCC')),
                  ("Pressure", '(Pa)', 'Entry', 'POS_NUM_ONLY'), 
                  ("Temperature", '(K)', 'Entry', 'POS_NUM_ONLY'),
                  ("Radius", '(\u00C5)', 'Entry', 'POS_NUM_ONLY')]
        gridSz =  wx.FlexGridSizer(3, 6, 8, 16)
        for (label, unit, widget_type, dlc) in items:
            gridSz.Add(wx.StaticText(self, label=label+unit), 
                       0, wx.ALIGN_CENTER_HORIZONTAL)
            if widget_type == 'Entry':
                wgt = wx.TextCtrl(self, -1, size=(120, -1), style=wx.TE_CENTRE)
                wgt.SetValidator(self.posDigitValidator)
            elif widget_type == 'Combobox':
                wgt = wx.ComboBox(self, -1, choices=dlc, value=dlc[0], 
                                  size=(120, -1), style=wx.CB_READONLY|wx.TE_CENTER)
            gridSz.Add(wgt, 0, wx.EXPAND)
            self.entries[label] = wgt

        self.Box.AddSpacer(8)
        self.Box.Add(gridSz, 0, wx.EXPAND, 5)

    def __InitOnoff(self):
        font = wx.Font(12,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_NORMAL,
                       False, 'Calibri')
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
        return  ("Text files (*.txt)|*.txt|"
                 "JSON files (*.json)|*.json|"
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
            self.log.WriteText(f"Inputs are saved as {path}.")
        dlg.Destroy()

    def OnLoad(self):
        dlg = wx.FileDialog(self, message="Choose a file",
                            wildcard=self.__getwildcard(),
                            style=wx.FD_OPEN | wx.FD_PREVIEW |
                            wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            with open(path, 'r') as f:
                values = json.load(f)
            print(values)
            for key, widget in self.entries.items():
                if (values.get(key)):
                    widget.SetValue(values[key])
            if values.get('flag_MSR') and values.get('MSR'):
                # print('loading msr')
                self.msrPane.Collapse(False)
                self.msrRunBtn.Enable()
                self.msrPane.onLoad(values['MSR'])
            if values.get('flag_KMC') and values.get('KMC'):
                self.kmcPane.Collapse(False)
                self.kmcRunBtn.Enable()
                self.kmcPane.OnLoad(values['KMC'])
            self.log.WriteText(f"Inputs are loaded from {path}.")
        dlg.Destroy()
    
    def OnClear():
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
                self.log.write(wulff.record_df)
                sj_elapsed = round(time.time() - sj_start, 4)
                q = 'MSR Job Completed. Total Cost About: ' + str(sj_elapsed) + ' Seconds\n'\
                    + 'Visulize the NanoParticles?'
                dlg = wx.MessageDialog(self, q, "Visualized?",
                                       style=wx.YES_NO|wx.ICON_INFORMATION)
                if dlg.ShowModal() == wx.ID_YES:
                    NP = NanoParticle(wulff.eles, wulff.positions, wulff.siteTypes)
                    NP.setColors(coltype='site_type')
                    self.topWin.glPanel.DrawNP(NP)
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
        pass

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
        self.__initGasesBox()
        self.Box.AddSpacer(8)
        self.__initFacesBox()

    def __initGasesBox(self):
        gasBox = wx.StaticBox(self.win, -1, 'Gases Info')
        gasSizer = wx.StaticBoxSizer(gasBox, wx.VERTICAL)
        self.Box.Add(gasSizer, 0, wx.EXPAND|wx.ALL)
        gasGridS = wx.FlexGridSizer(4, 5, 8, 16)
        gasSizer.Add(gasGridS, 0, wx.EXPAND|wx.ALL)

        gasGridS.Add(wx.StaticText(self.win, label=''))
        gasGridS.Add(wx.StaticText(self.win, label='Name'), 0,  wx.ALIGN_CENTER_HORIZONTAL)
        gasGridS.Add(wx.StaticText(self.win, label='Partial Pressure (%)'), 0,  wx.ALIGN_CENTER_HORIZONTAL)
        gasGridS.Add(wx.StaticText(self.win, label='Gas Entropy (eV/K)'), 0,  wx.ALIGN_CENTER_HORIZONTAL)
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
            print(e)

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
        self.li = np.array([[]])
        # a bidirectional map between reactant and id
        self.id2reactantMap = bidict.bidict({0: "*"})   

        self.win = self.GetPane()
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.win.SetSizerAndFit(self.Box)
        
        nSpe = 1
        self.__initUI()
        self.__initSpecies()
        self.__initProducts()
        self.__initEvents()
        self.__initLi(nSpe)
        self.spePane.setSpes(nSpe)
    
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

    def __initLi(self, nSpe):
        liSz = wx.BoxSizer(wx.HORIZONTAL)
        self.Box.Add(liSz, 0, wx.EXPAND|wx.ALL, 4)
        liSz.AddSpacer(self.padding)
        liSz.Add(wx.StaticText(self.win, label='Lateral interacion (eV): '), 
                 0, wx.ALIGN_CENTER|wx.ALL)
        liBtn = wx.Button(self.win, -1, "Set")
        self.liWin = popupLiInSpe(self, nSpe)
        liBtn.Bind(wx.EVT_BUTTON, lambda event: self.__onShowPopup(event, self.liWin))
        liSz.AddSpacer(8)
        liSz.Add(liBtn, 0, wx.ALIGN_CENTER|wx.ALL)

    def __onShowPopup(self, event, win):
        btn = event.GetEventObject()
        pos = btn.ClientToScreen( (0,0) )
        sz =  btn.GetSize()
        
        win.Position(pos, (0, sz[1]))
        win.Popup(focus=win)

    def updateIdMap(self, id, name):
        try:
            self.id2reactantMap[id] = f"{name}*"
            for evtRow in np.append(self.evtPane.mobRows, self.evtPane.fixRows):
                evtRow.updateReactants()
        except bidict.ValueDuplicationError:
            self.log.WriteText("Please ensure the unique of name")
        print(self.id2reactantMap)
    
    def popIdMap(self, id):
        self.id2reactantMap.pop(id)
        for evtRow in np.append(self.evtPane.mobRows, self.evtPane.fixRows):
            evtRow.updateReactants()
        print(self.id2reactantMap)

    def OnSave(self):
        for key, widget in self.entries.items():
            self.values[key] = widget.GetValue()
        self.values['nspecies'] = self.nspecies
        for i, spe in enumerate(self.species):
            self.values[f"s{i+1}"] = json.dumps(spe, cls=Specie.Encoder)
        pass
        return self.values

    def OnLoad(self, values : dict):
        self.values = values
        for key, widget in self.entries.items():
            widget.SetValue(self.values.get(key, ''))
        if self.values.get('nspecies'):
            self.spePane.setSpes(nSpe=self.values['nspecies'])
            self.parent.OnInnerSizeChanged()
        pass

    def OnGroupStrSelect(self, event):
        radio_selected = event.GetEventObject()
        print('EvtRadioBox: %s' % radio_selected.Name)


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
        newSpe = Specie(f"Specie{self._nSpes}")
        id = self._nSpes
        newRow = SpecieRow(self, id, newSpe)
        self.box.Add(newRow, 0, wx.EXPAND|wx.ALL, 4)
        self.rows = np.append(self.rows, newRow)
        self.master.species = np.append(self.master.species, newSpe)

        self.master.updateIdMap(id, newSpe.getName()) ##
    
    def __add(self, event):
        self.__addSpe()
        self.speLabel.SetLabel(f"{self._nSpes}")
        self.master.GetParent().OnInnerSizeChanged()

    def __delSpe(self):
        if self._nSpes > 1:
            id = self._nSpes
            self.master.popIdMap(id) ##
            self.master.nspecies -= 1
            self._nSpes -= 1
            lastRow, self.rows = self.rows[-1], self.rows[:-1]
            lastSpe, self.master.species = self.master.species[-1], self.master.species[:-1]
            lastRow.delete()
            del lastRow
            del lastSpe
            return True
        return False

    def __del(self, event):
        if self.__delSpe():
            self.speLabel.SetLabel(f"{self._nSpes}")
            # self.master.Layout()
            self.master.GetParent().OnInnerSizeChanged()
        pass
  
    def setSpes(self, nSpe: int):
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
        print(self._rowDict)
        self._evtDict = {}

        self.subEntries = {}
        self.subBox = wx.GridBagSizer(vgap=4, hgap=16)
        self.SetSizer(self.subBox)
        self.__initUI()
        self.__SetValues()

    def __initUI(self):
        col = 0
        nameEty = wx.TextCtrl(self, -1, size=(100, -1), style=wx.TE_CENTER)
        nameEty.Bind(wx.EVT_TEXT, lambda event: self.onTextChange(event, self.sepcie, 'name'))
        self.subEntries["name"] = nameEty
        self.subBox.Add(nameEty, pos=(0, col), span=(2, 1), flag=wx.ALIGN_CENTER|wx.ALL)
        
        col += 1
        self.subBox.Add(wx.StaticText(self, label=""), pos=(0, col), span=(2, 1))

        col += 1
        siteBox = wx.BoxSizer(wx.HORIZONTAL)
        msg = "Turning on when specie occupies two adsorption sites."
        siteOnOff = oob.OnOffButton(self, -1, "Two-site", initial=0, name="is_twosite")
        siteOnOff.SetBackgroundColour(BG_COLOR)
        siteOnOff.SetFont(GET_FONT())
        self.subEntries["is_twosite"] = siteOnOff
        siteBox.Add(siteOnOff, 0)
        staticInfoBmp = wx.StaticBitmap(self, -1, GET_INFO_BMP())
        staticInfoBmp.SetToolTip(msg)
        siteBox.Add(staticInfoBmp, 0, wx.ALIGN_CENTER)
        self.subBox.Add(siteBox, pos=(0, col), flag=wx.ALIGN_CENTER|wx.ALL)
        siteBtn = wx.Button(self, -1, "Set", size=(80, -1))
        self._btnDict["is_twosite"] = siteBtn
        self.subBox.Add(siteBtn, pos=(1, col), flag=wx.ALIGN_CENTER|wx.ALL)

        col += 1
        self.subBox.Add(wx.StaticText(self, label=""), pos=(0, col), span=(2, 1))

        col += 1
        adsOnoff = oob.OnOffButton(self, -1, "Adsorption", initial=0, name="flag_ads")
        adsOnoff.SetBackgroundColour(BG_COLOR)
        adsOnoff.SetFont(GET_FONT())
        self.subEntries["flag_ads"] = adsOnoff
        self.subBox.Add(adsOnoff, pos=(0, col), flag=wx.ALIGN_CENTER|wx.ALL)
        desOnoff = oob.OnOffButton(self, -1, "Desorption", initial=0, name="flag_des")
        desOnoff.SetBackgroundColour(BG_COLOR)
        desOnoff.SetFont(GET_FONT())
        self.subEntries["flag_des"] = desOnoff
        self.subBox.Add(desOnoff, pos=(0, col+1), flag=wx.ALIGN_CENTER|wx.ALL)
        adsDesBtn = wx.Button(self, -1, "Set", size=(120, -1))
        self.subBox.Add(adsDesBtn, pos=(1, col), span=(1, 2), flag=wx.ALIGN_CENTER|wx.ALL)
        self.adsDesWin = popupAdsDesInSpe(self)
        adsDesBtn.Bind(wx.EVT_BUTTON, lambda event: self.__onShowPopup(event, self.adsDesWin))
        self._btnDict["flag_ads"] = adsDesBtn
        self._btnDict["flag_des"] = adsDesBtn

        col += 2
        self.subBox.Add(wx.StaticText(self, label=""), pos=(0, col), span=(2, 1))

        col += 1
        diffOnOff = oob.OnOffButton(self, -1, "Diffusion", initial=0, name="flag_diff")
        diffOnOff.SetBackgroundColour(BG_COLOR)
        diffOnOff.SetFont(GET_FONT())
        self.subBox.Add(diffOnOff, pos=(0, col), flag=wx.ALIGN_CENTER|wx.ALL)
        self.subEntries["flag_diff"] = diffOnOff
        diffBtn = wx.Button(self, -1, "Set", size=(80, -1))
        self.subBox.Add(diffBtn, pos=(1, col), flag=wx.ALIGN_CENTER|wx.ALL)
        self._btnDict["flag_diff"] = diffBtn

        self.Bind(oob.EVT_ON_OFF, self.__SwOnOff)
    
    def __SwOnOff(self, event):
        obj = event.GetEventObject()
        name = obj.Name
        self.onTextChange(event, self.sepcie, name)
        if (name == "is_twosite"):
            if obj.GetValue():
                self.subEntries["flag_diff"].Disable()
                self._btnDict["flag_diff"].Disable()
                if self._rowDict["flag_diff"]:
                    self.master.evtPane.delFixEvt(self._rowDict["flag_diff"])
                    self._rowDict["flag_diff"] = None
            else:
                self.subEntries["flag_diff"].Enable()
                self._btnDict["flag_diff"].Enable(self.subEntries["flag_diff"].GetValue())
            pass
        else:
            self._btnDict[name].Enable(obj.GetValue())
            if obj.GetValue():
                evt = self._evtDict[name]
                self._rowDict[name] = self.master.evtPane.addFixEvt(evt)
            else:
                row = self._rowDict[name]
                if row:
                    self.master.evtPane.delFixEvt(row)
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

    def __SetEvts(self, name : str):
        self._evtDict["flag_ads"] = Event(
            name=f"{name}-ads", type="Adsorption", is_twosite=False, 
            cov_before=[0, 0], cov_after=[self.id, 0])
        self._evtDict["flag_des"] = Event(
            name=f"{name}-des", type="Desorption", is_twosite=False, 
            cov_before=[self.id, 0], cov_after=[0, 0])
        self._evtDict["flag_diff"] = Event(
            name=f"{name}-diff", type="Diffusion", is_twosite=True, 
            cov_before=[self.id, 0], cov_after=[0, self.id])
    
    def __ChangeEvtsName(self, name : str):
        self._evtDict["flag_ads"].name = f"{name}-ads"
        self._evtDict["flag_des"].name = f"{name}-des"
        self._evtDict["flag_diff"].name = f"{name}-diff"

    def onTextChange(self, event, instance:Specie, attr:str):
        value = event.GetEventObject().GetValue()
        setattr(instance, attr, value)
        if attr == "name":
            self.master.updateIdMap(self.id, instance.getName())
            self.__ChangeEvtsName(instance.getName())
        # print(instance)
    
    """ def setNameEtyBG(self, flag):
        if flag:
            self.subEntries["name"].SetBackgroundColour(BG_COLOR)
        else:
            self.subEntries["name"].SetBackgroundColour(WARNING_COLOR) """

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
            wx.StaticText(panel, label='Entropy (eV/T) -- of adsorbed specie'), 
            0, wx.ALIGN_CENTER|wx.ALL, 8
        )
        SadsEty = wx.TextCtrl(panel, -1, size=(100, -1), style=wx.TE_CENTER, name="S_ads")
        SadsEty.SetValidator(parent.digitValidator)
        SadsEty.Bind(wx.EVT_TEXT, lambda event: parent.onTextChange(event, parent.sepcie, 'S_ads'))
        self.entries['S_ads'] = SadsEty
        boxh2.Add(SadsEty, 0, wx.ALL, 8)
        boxh2.Add(
            wx.StaticText(panel, label=' -- of gas-phase specie'), 
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


class popupLiInSpe(wx.PopupTransientWindow):
    def __init__(self, parent : KmcPanel, nSpe, style=wx.SIMPLE_BORDER|wx.PU_CONTAINS_CONTROLS):
        wx.PopupTransientWindow.__init__(self, parent, style)
        self.SetBackgroundColour(POP_BG_COLOR)
        self.SetFont(GET_FONT())
        self.parent = parent
        self.nSpe = nSpe
        self.panel = wx.Panel(parent.win)
        self.mainbox = wx.GridBagSizer(hgap=0, vgap=4)
        self.panel.SetSizer(self.mainbox)

        self.layerEtys = {}
        self.Labels = np.array([f"Specie{i+1}" for i in range(nSpe)])
        self.__initUI()
    
    def __initUI(self):
        pass
        self.mainbox.Fit(self.panel)
        self.mainbox.Fit(self)
        self.Layout()

    def addSpe(self):
        pass

    def delSpe(self):
        pass

    def setLabels(self):
        pass

    def setValues(self):
        pass

    def getValues(self):
        pass


class ProductPane(wx.Panel):
    def __init__(self, master : KmcPanel, parent):
        wx.Panel.__init__(self, parent, name="proPane")
        self.master = master
        self.Texts = np.array([])

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

        self.box = wx.BoxSizer(wx.HORIZONTAL) # box to put products name
        mainBox.Add(self.box, 0, wx.EXPAND|wx.ALL)
        self.box.AddSpacer(self.master.padding)
    
    def __add(self, event):
        pass

    def __del(self, event):
        pass


class EventPane(wx.Panel):
    def __init__(self, master : KmcPanel, parent):
        wx.Panel.__init__(self, parent, name="evtPane")
        self.master = master
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
        pass

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
        pass
        
    def __refersh(self):
        self.evtLabel.SetLabel(f"{self.master.nevents}")
        self.master.GetParent().OnInnerSizeChanged()
    
    def addFixEvt(self, evt):
        # create by toggle in specieRow
        newRow = self.__addEvt(self.fixEvtBox, evt)
        self.fixRows = np.append(self.fixRows, newRow)
        newRow.SetWindowStyle(wx.BORDER_SUNKEN)
        newRow.setFix()
        self.__refersh()
        return newRow
    
    def delFixEvt(self, row):
        # create by toggle in specieRow
        self.fixRows = self.fixRows[self.fixRows != row]
        row.delete()
        self.__refersh()


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
        self.subBox.Add(nameEty, 0, wx.ALIGN_CENTER, 4)

        self.subBox.AddSpacer(self.padding)
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
        self.subBox.Add(sitePane, 0, wx.ALIGN_CENTER, 4)

        self.subBox.AddSpacer(self.padding)
        typeCombo = wx.ComboBox(
            self, -1, choices=self._types, value=self._types[-1],
            size=(100, -1), style=wx.CB_READONLY, name="type")
        typeCombo.Bind(wx.EVT_COMBOBOX, self.__OnType)
        self.subEntries["type"] = typeCombo
        self.subBox.Add(typeCombo, 0, wx.ALIGN_CENTER, 4)

        self.subBox.AddSpacer(self.padding)
        RiCombo = wx.ComboBox(
            self, -1, choices=self._reactants, value=self._reactants[0],
            size=(self.width, -1), style=wx.CB_READONLY, name="R0")
        RiCombo.Bind(wx.EVT_COMBOBOX, self.__OnReactant)
        self.subBox.Add(RiCombo, 0, wx.ALIGN_CENTER, 4)
        self.subBox.AddSpacer(self.padding)
        RjCombo = wx.ComboBox(
            self, -1, choices=self._reactants, value=self._reactants[0],
            size=(self.width, -1), style=wx.CB_READONLY, name="R1")
        RjCombo.Bind(wx.EVT_COMBOBOX, self.__OnReactant)
        self.subBox.Add(RjCombo, 0, wx.ALIGN_CENTER, 4)
        self.subEntries["cov_before"] = [RiCombo, RjCombo]
        
        self.subBox.AddSpacer(self.padding)
        PiCombo = wx.ComboBox(
            self, -1, choices=self._reactants, value=self._reactants[0],
            size=(self.width, -1), style=wx.CB_READONLY, name="P0")
        PiCombo.Bind(wx.EVT_COMBOBOX, self.__OnReactant)
        self.subBox.Add(PiCombo, 0, wx.ALIGN_CENTER, 4)
        self.subBox.AddSpacer(self.padding)
        PjCombo = wx.ComboBox(
            self, -1, choices=self._reactants, value=self._reactants[0],
            size=(self.width, -1), style=wx.CB_READONLY, name="P1")
        PjCombo.Bind(wx.EVT_COMBOBOX, self.__OnReactant)
        self.subBox.Add(PjCombo, 0, wx.ALIGN_CENTER, 4)
        self.subEntries["cov_after"] = [PiCombo, PjCombo]

        self.subBox.AddSpacer(self.padding)
        subpane = wx.Panel(self, size=(110, -1))
        # subpane.SetBackgroundColour("pink")
        subbox = wx.BoxSizer(wx.HORIZONTAL)
        subpane.SetSizer(subbox)
        self.BEPrBtn = wx.Button(subpane, -1, 'Set')
        subbox.Add(self.BEPrBtn, 0)
        self.subBox.Add(subpane, 0, wx.ALIGN_CENTER, 4)
        pass
    
    def __OnType(self, event):
        obj = event.GetEventObject()
        name = obj.Name
        self.onTextChange(event, self.event, name)
        pass

    def __OnReactant(self, event):
        obj = event.GetEventObject()
        name = obj.Name
        value = self.master.id2reactantMap.inverse[obj.GetValue()]
        print(value)
        self.onTextChange(event, self.event, name, value)
        pass

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
        print(evt)
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
        print(instance)

    def updateReactants(self):
        self._reactants = list(self.master.id2reactantMap.values())
        print('update evt: ', self._reactants)
        for key in ["cov_before", "cov_after"]:
            combos = self.subEntries[key]
            values = getattr(self.event, key)
            for i in [0, 1]:
                combos[i].Set(self._reactants)
                name = self.master.id2reactantMap.get(values[i], "*")
                combos[i].SetValue(name)
        pass

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