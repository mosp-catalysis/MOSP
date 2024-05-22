"""
@author: yinglei
"""

import wx
import wx.grid
import json
import time
import numpy as np
from utils.msr import Wulff
try:
    import views.onoffbutton as oob
    from views.particle import NanoParticle
    from views.dataclass import Specie, Product, Event
except:
    import onoffbutton as oob
    from particle import NanoParticle
    from dataclass import Specie, Product, Event

BG_COLOR = 'white'
POP_BG_COLOR = '#FFFAEF'

def GET_FONT():
    FONT = wx.Font(
        12, wx.FONTFAMILY_DEFAULT,
        wx.FONTSTYLE_NORMAL,
        wx.FONTWEIGHT_NORMAL,
        False, 'Calibri')
    return FONT

class MyValidator(wx.Validator):
    def __init__(self, flag, infoBar=None, log=None):
        wx.Validator.__init__(self)
        # self.LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.NUMS = '-0123456789.'
        self.POS_NUMS = '0123456789.'
        self.flag = flag
        self.infoBar = infoBar
        self.log = log
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return MyValidator(self.flag, self.infoBar, self.log)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()

        """ if self.flag == 'ALPHA_ONLY':
            for x in val:
                if x not in self.LETTERS:
                    return False """
        if self.flag == 'NUM_ONLY':
            for x in val:
                if x not in self.NUMS:
                    return False
        elif self.flag == 'POS_NUM_ONLY':
            for x in val:
                if x not in self.POS_NUMS:
                    return False
        return True

    def OnChar(self, event):
        key = event.GetKeyCode()

        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return

        if self.flag == 'ALPHA_ONLY' and chr(key) in self.LETTERS:
            event.Skip()
            return

        if self.flag == 'NUM_ONLY' and chr(key) in self.NUMS:
            event.Skip()
            return
        
        if self.flag == 'POS_NUM_ONLY' and chr(key) in self.POS_NUMS:
            event.Skip()
            return

        if not wx.Validator.IsSilent():
            wx.Bell()
            if self.flag == 'POS_NUM_ONLY':
                mes = 'Please enter positive number.'
            elif self.flag == 'NUM_ONLY':
                mes = 'Please enter digitals.'
            elif self.flag == 'ALPHA_ONLY':
                mes = 'Please enter letters.'
            if self.infoBar:
                self.infoBar.ShowMessage(mes, wx.ICON_INFORMATION)
            if self.log:
                self.log.WriteText(mes)

        # Returning without calling even.Skip eats the event before it
        # gets to the text control
        return


class InputPanel(wx.ScrolledWindow):
    def __init__(self, parent, topWin, log=None):
        wx.ScrolledWindow.__init__(self, parent)
        self.topWin = topWin
        self.log = log
        self.infoBar = wx.InfoBar(self)
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.Box)
        self.Box.Add(self.infoBar, 0, wx.EXPAND, 5)

        self.digitValidator = MyValidator('NUM_ONLY', log=self.log)
        self.posDigitValidator = MyValidator('POS_NUM_ONLY', log=self.log)

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
            pass

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
            for key, widget in self.entries.items():
                widget.SetValue(values.get(key))
            if values.get('flag_MSR') and values.get('MSR'):
                # print('loading msr')
                self.msrPane.onLoad(values['MSR'])
            if values.get('flag_KMC') and values.get('KMC'):
                pass
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

    def setFaces(self, nFaces):
        if nFaces < 1:
            return
        while(self.nFaces != nFaces):
            if (self.nFaces > nFaces):
                self.__delFace()
            if (self.nFaces < nFaces):
                self.__addFace()
        for i in range(nFaces):
            if self.values.get(f"Face{i+1}"):
                subvalues = self.values[f"Face{i+1}"]
                self.faceRows[i].setValues(subvalues)
            self.faceLabel.SetLabel(f"{self.nFaces}")

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
        self.digitValidator = parent.digitValidator
        self.posDigitValidator = parent.posDigitValidator
        self.win = self.GetPane()
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.win.SetSizerAndFit(self.Box)
        self.parent = parent
        self.entries = {}
        self.msrFlag = True
        self.iniFilePath = ""

        self.nspecies = 0
        self.nproducts = 0
        self.nevents = 0
        self.species = np.array([])
        self.products = np.array([])
        self.events = np.array([])
        self.li = np.array([[]])
        self.id2reactantMap = {}   # act as a hash map between reactant and id

        self.__initUI()
    
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

        self.__initSpecies()
        self.__initProducts()
        self.__initEvents()

    def __initSpecies(self):
        speBox = wx.StaticBox(self.win, -1, '')
        speSizer = wx.StaticBoxSizer(speBox, wx.VERTICAL)
        self.Box.Add(speSizer, 0, wx.EXPAND|wx.ALL)

        self.spePane = SpeciePane(self, self.win)
        speSizer.Add(self.spePane)

    def __initProducts(self):
        pass

    def __initEvents(self):
        pass

    def OnGroupStrSelect(self, event):
        radio_selected = event.GetEventObject()
        print('EvtRadioBox: %s' % radio_selected.Name)


class SpeciePane(wx.Panel):
    def __init__(self, master : KmcPanel, parent):
        wx.Panel.__init__(self, parent, name="spePane")
        # self.SetScrollRate(10, 10)
        self.rows = np.array([])

        self.master = master
        self.box = wx.BoxSizer(wx.VERTICAL) 
        self.SetSizer(self.box)

        buttonSz = wx.BoxSizer(wx.HORIZONTAL)
        buttonSz.AddSpacer(self.master.padding)
        self.speLabel = wx.StaticText(self, label=f"{self.master.nspecies}")
        addBtn = wx.Button(self, -1, 'Add')
        self.Bind(wx.EVT_BUTTON, self.__add, addBtn)
        delBtn = wx.Button(self, -1, 'Delete')
        self.Bind(wx.EVT_BUTTON, self.__del, delBtn)
        buttonSz.Add(wx.StaticText(self, label='Number of adsorbed species: '), 
                     0, wx.ALIGN_CENTER|wx.ALL)
        buttonSz.Add(self.speLabel, 0, wx.ALIGN_CENTER|wx.ALL)
        buttonSz.AddSpacer(16)
        buttonSz.Add(addBtn, 0, wx.ALIGN_CENTER|wx.ALL)
        buttonSz.AddSpacer(16)
        buttonSz.Add(delBtn, 0, wx.ALIGN_CENTER|wx.ALL)
        self.box.Add(buttonSz, 0, wx.EXPAND|wx.ALL, 4)

    def __addSpe(self):
        self.master.nspecies += 1
        newSpe = Specie(f"Specie{self.master.nspecies}")
        newRow = SpecieRow(self, newSpe)
        self.box.Add(newRow, 0, wx.EXPAND|wx.ALL, 4)
        self.rows = np.append(self.rows, newRow)
        self.master.species = np.append(self.master.species, newSpe)
        pass
    
    def __add(self, event):
        self.__addSpe()
        self.speLabel.SetLabel(f"{self.master.nspecies}")
        self.master.GetParent().OnInnerSizeChanged()

    def __delSpe(self):
        if self.master.nspecies > 1:
            self.master.nspecies -= 1
            lastRow, self.rows = self.rows[-1], self.rows[:-1]
            lastSpe, self.master.species = self.master.species[-1], self.master.species[:-1]
            lastRow.delete()
            del lastRow
            del lastSpe
            return True
        return False

    def __del(self, event):
        if self.__delSpe():
            self.speLabel.SetLabel(f"{self.master.nspecies}")
            # self.master.Layout()
            self.master.GetParent().OnInnerSizeChanged()
        pass


class SpecieRow(wx.Panel):
    def __init__(self, parent : SpeciePane, spe : Specie):
        wx.Panel.__init__(self, parent)
        self.sepcie = spe
        self.digitValidator = parent.master.digitValidator
        self.posDigitValidator = parent.master.posDigitValidator

        self.subEntries = {}
        self.btnDict = {}
        self.subBox = wx.GridBagSizer(vgap=4, hgap=16)
        self.SetSizer(self.subBox)

        col = 0
        nameEty = wx.TextCtrl(self, -1, size=(100, -1), style=wx.TE_CENTER)
        nameEty.Bind(wx.EVT_TEXT, lambda event: self.onTextChange(event, self.sepcie, 'name'))
        self.subEntries["name"] = nameEty
        self.subBox.Add(nameEty, pos=(0, col), span=(2, 1), flag=wx.ALIGN_CENTER|wx.ALL)
        
        col += 1
        self.subBox.Add(wx.StaticText(self, label=""), pos=(0, col), span=(2, 1))

        col += 1
        msg = "Turning on when this specie occupies two adsorption sites."
        siteOnOff = oob.OnOffButton(self, -1, "Two-site", initial=0, name="is_twosite")
        siteOnOff.SetBackgroundColour(BG_COLOR)
        siteOnOff.SetFont(GET_FONT())
        siteOnOff.SetToolTip(msg)
        self.subEntries["is_twosite"] = siteOnOff
        self.subBox.Add(siteOnOff, pos=(0, col), flag=wx.ALIGN_CENTER|wx.ALL)
        siteBtn = wx.Button(self, -1, "Set", size=(80, -1))
        self.btnDict["is_twosite"] = siteBtn
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
        self.adsDesWin = popupAdsDesInKmc(self)
        adsDesBtn.Bind(wx.EVT_BUTTON, lambda event: self.__onShowPopup(event, self.adsDesWin))
        self.btnDict["flag_ads"] = adsDesBtn
        self.btnDict["flag_des"] = adsDesBtn

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
        self.btnDict["flag_diff"] = diffBtn


        self.Bind(oob.EVT_ON_OFF, self.__SwOnOff)
        self.SetValues()
    
    def __SwOnOff(self, event):
        obj = event.GetEventObject()
        name = obj.Name
        self.onTextChange(event, self.sepcie, name)
        if (name == "is_twosite"):
            pass
        else:
            if (obj.GetValue()):
                self.btnDict[name].Enable()
            else:
                self.btnDict[name].Disable()

    
    def __onShowPopup(self, event, win):
        btn = event.GetEventObject()
        pos = btn.ClientToScreen( (0,0) )
        sz =  btn.GetSize()
        
        win.Position(pos, (0, sz[1]))
        win.Popup(focus=win)
    
    def onTextChange(self, event, instance, attr):
        value = event.GetEventObject().GetValue()
        setattr(instance, attr, value)
        print(instance)

    def SetValues(self):
        spe = self.sepcie
        self.subEntries["name"].SetHint(spe.default_name)
        if spe.name:
            self.subEntries["name"].SetValue(spe.name)
        self.subEntries["flag_ads"].SetValue(spe.flag_ads)
        self.subEntries["flag_des"].SetValue(spe.flag_des)
        if not (spe.flag_ads or spe.flag_des):
            self.btnDict["flag_ads"].Disable()
        self.subEntries["flag_diff"].SetValue(spe.flag_diff)
        if not spe.flag_diff:
            self.btnDict["flag_diff"].Disable()
        self.subEntries["is_twosite"].SetValue(spe.is_twosite)
        if not spe.is_twosite:
            pass

    def delete(self):
        """ for widget in self.subEntries.values():
            widget.Destroy() """
        self.Destroy()


class popupAdsDesInKmc(wx.PopupTransientWindow):
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
        mainbox.Add(boxh1, 0, wx.EXPAND|wx.ALL)
        mainbox.Add(boxh2, 0, wx.EXPAND|wx.ALL)
        
        boxh1.Add(
            wx.StaticText(panel, label='Molecular mass'), 
            0, wx.ALIGN_CENTER|wx.ALL, 8
        )
        massEty = wx.TextCtrl(panel, -1, size=(100, -1), style=wx.TE_CENTER, name="mass")
        massEty.SetValidator(parent.posDigitValidator)
        massEty.Bind(wx.EVT_TEXT, lambda event: parent.onTextChange(event, parent.sepcie, 'mass'))
        boxh1.Add(massEty, 0, wx.ALL, 8)
        boxh1.Add(
            wx.StaticText(panel, label='Pressure fracion (%)'), 
            0, wx.ALIGN_CENTER|wx.ALL, 8
        )
        ppEty = wx.TextCtrl(panel, -1, size=(100, -1), style=wx.TE_CENTER, name="PP_ratio")
        ppEty.SetValidator(parent.posDigitValidator)
        ppEty.Bind(wx.EVT_TEXT, lambda event: parent.onTextChange(event, parent.sepcie, 'PP_ratio'))
        boxh1.Add(ppEty, 0, wx.ALL, 8)

        boxh2.Add(
            wx.StaticText(panel, label='Entropy (eV/T) -- of adsorbed specie'), 
            0, wx.ALIGN_CENTER|wx.ALL, 8
        )
        SadsEty = wx.TextCtrl(panel, -1, size=(100, -1), style=wx.TE_CENTER, name="S_ads")
        SadsEty.SetValidator(parent.digitValidator)
        SadsEty.Bind(wx.EVT_TEXT, lambda event: parent.onTextChange(event, parent.sepcie, 'S_ads'))
        boxh2.Add(SadsEty, 0, wx.ALL, 8)
        boxh2.Add(
            wx.StaticText(panel, label=' -- of gas-phase specie'), 
            0, wx.ALIGN_CENTER|wx.ALL, 8
        )
        SgasEty = wx.TextCtrl(panel, -1, size=(100, -1), style=wx.TE_CENTER, name="S_gas")
        SgasEty.SetValidator(parent.digitValidator)
        SgasEty.Bind(wx.EVT_TEXT, lambda event: parent.onTextChange(event, parent.sepcie, 'S_gas'))
        boxh2.Add(SgasEty, 0, wx.ALL, 8)

        mainbox.Fit(panel)
        mainbox.Fit(self)
        self.Layout()

