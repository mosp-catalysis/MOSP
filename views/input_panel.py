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
except:
    import onoffbutton as oob
    from particle import NanoParticle


class MyValidator(wx.Validator):
    def __init__(self, flag, infoBar):
        wx.Validator.__init__(self)
        # self.LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.NUMS = '-0123456789.'
        self.POS_NUMS = '0123456789.'
        self.flag = flag
        self.infoBar = infoBar
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return MyValidator(self.flag, self.infoBar)

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

        # Returning without calling even.Skip eats the event before it
        # gets to the text control
        return


class InputPanel(wx.ScrolledWindow):
    def __init__(self, parent, topWin, log):
        wx.ScrolledWindow.__init__(self, parent)
        self.topWin = topWin
        self.log = log
        self.infoBar = wx.InfoBar(self)
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.Box)
        self.Box.Add(self.infoBar, 0, wx.EXPAND, 5)

        self.digitValidator = MyValidator('NUM_ONLY', self.infoBar)
        self.posDigitValidator = MyValidator('POS_NUM_ONLY', self.infoBar)

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
        self.msrOnoff.SetBackgroundColour('white')
        self.msrOnoff.SetFont(font)
        self.kmcOnoff = oob.OnOffButton(self, -1, "Enabling KMC",
                                        initial = 1, 
                                        name="kmcOnoff")
        self.kmcOnoff.SetBackgroundColour('white')
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
    
    def __InitMSR(self):
        self.msrPane = MsrPanel(self)
        self.msrPane.Collapse(False)
        self.Box.Add(self.msrPane, 0, wx.ALL|wx.EXPAND)

    def __InitKMC(self):
        self.kmcPane = KmcPanel(self)
        self.kmcPane.Collapse(False)
        self.Box.Add(self.kmcPane, 0, wx.ALL|wx.EXPAND)

    def __SwOn(self, event):
        obj = event.GetEventObject()
        if obj.Name == 'msrOnoff':
            if self.msrPane.IsCollapsed:
                self.msrPane.Collapse(False)
                self.Layout()
            self.msrRunBtn.Enable()
        elif obj.Name == 'kmcOnoff':
            if self.kmcPane.IsCollapsed:
                self.kmcPane.Collapse(False)
                self.Layout()
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
        self.Layout()

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
                print('loading msr')
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
        self.win = self.GetPane()
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.win.SetSizerAndFit(self.Box)
        self.parent = parent
        self.nGas = 3
        self.nFaces = 0
        self.initFace = 3
        self.faceRows = np.array([])
        # self.win.SetBackgroundColour('#f0f0f0')
        
        self.entries = {}
        self.values = {}
        self.__Init_GasesBox()
        self.Box.AddSpacer(8)
        self.__Init_FacesBox()

    def __Init_GasesBox(self):
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
                    ety.SetValidator(self.parent.posDigitValidator)
            styles = ['Associative', 'Dissociative']
            combo = wx.ComboBox(self.win, -1, choices=styles, value=styles[0], 
                                size=(120, -1), style=wx.CB_READONLY)
            self.entries[f"Gas{i}_type"] = combo
            gasGridS.Add(combo, 0, wx.EXPAND)
        gasSizer.AddSpacer(4)

    def __Init_FacesBox(self):
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
        indexCtrl.SetValidator(parent.parent.digitValidator)
        self.sizer.Add(indexCtrl, pos=(idx, 0),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.subentries['index'] = indexCtrl

        gammaCtrl = wx.TextCtrl(master, -1, size=(120, -1), style=wx.TE_CENTRE, name='index')
        gammaCtrl.SetValidator(parent.parent.posDigitValidator)
        self.sizer.Add(gammaCtrl, pos=(idx, 1),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.subentries['gamma'] = gammaCtrl

        EadsBtn = wx.Button(master, -1, "Set", size=(120, -1))
        self.EadsWin = popupAdsInFace(parent)
        self.sizer.Add(EadsBtn, pos=(idx, 2),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.subentries['E_ads'] = self.EadsWin.entries
        EadsBtn.Bind(wx.EVT_BUTTON, lambda event: self.onShowPopup(event, self.EadsWin))
        self.entries.append(EadsBtn)

        SadsBtn = wx.Button(master, -1, "Set", size=(120, -1))
        self.SadsWin = popupAdsInFace(parent)
        self.sizer.Add(SadsBtn, pos=(idx, 3),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.subentries['S_ads'] = self.SadsWin.entries
        SadsBtn.Bind(wx.EVT_BUTTON, lambda event: self.onShowPopup(event, self.SadsWin))
        self.entries.append(SadsBtn)

        LIBtn = wx.Button(master, -1, "Set", size=(120, -1))
        self.LIWin = popupLiInFace(parent)
        self.sizer.Add(LIBtn, pos=(idx, 4),  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL)
        self.subentries['S_ads'] = self.LIWin.entries
        LIBtn.Bind(wx.EVT_BUTTON, lambda event: self.onShowPopup(event, self.LIWin))
        self.entries.append(LIBtn)
    
    def onShowPopup(self, event, win):
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

        self.delete


class popupAdsInFace(wx.PopupTransientWindow):
    def __init__(self, parent : MsrPanel, style=wx.SIMPLE_BORDER|wx.PU_CONTAINS_CONTROLS, nGas=3):
        wx.PopupTransientWindow.__init__(self, parent, style)
        # self.values = np.zeros(nGas)
        self.entries = []
        panel = wx.Panel(self)
        sz = wx.FlexGridSizer(nGas, 2, 0, 4)
        panel.SetSizer(sz)
        for i in range(nGas):
            sz.Add(wx.StaticText(panel, label=f"Gas{i+1}"), 0, wx.ALIGN_CENTER|wx.ALL, 6)
            ety = wx.TextCtrl(panel, -1, size=(80, -1), style=wx.TE_CENTER, name=f"{i}")
            ety.SetValue('0.00')
            ety.SetValidator(parent.parent.digitValidator)
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
                ety.SetValidator(parent.parent.digitValidator)
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
    def __init__(self, parent):
        wx.CollapsiblePane.__init__(self, parent, label='KMC', name='kmc')
        self.win = self.GetPane()
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.win.SetSizerAndFit(self.Box)
        self.parent = parent
        self.entries = {}
        self.initUI()
    
    def initUI(self):
        boxh1 = wx.BoxSizer(wx.HORIZONTAL)
        self.Box.Add(boxh1, 0, wx.EXPAND|wx.ALL)
        boxh1.AddSpacer(8)
        boxh1.Add(wx.StaticText(self.win, label='Initial structure: '), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        iniStrList = ['MSR Structure', 'Read from file']
        radio0 = wx.RadioButton(self.win, -1, iniStrList[0], name="msr")
        radio1 = wx.RadioButton(self.win, -1, iniStrList[1], name="file")
        iniStrCtrls = [radio0, radio1]
        boxh1.Add(radio0, 0, wx.ALIGN_CENTER|wx.ALL, 8)
        boxh1.Add(radio1, 0, wx.ALIGN_CENTER|wx.ALL, 8)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnGroupStrSelect, radio0)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnGroupStrSelect, radio1)
        """ iniStrRb = wx.RadioBox(self.win, -1, 
                               choices=iniStrList, 
                               wx.NO_BORDER)
        self.entries['iniStr'] = iniStrRb
        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, iniStrRb)
        boxh1.Add(iniStrRb, 0, wx.ALL) """

    def OnGroupStrSelect(self, event):
        radio_selected = event.GetEventObject()
        # print('EvtRadioBox: %s' % radio_selected.Name)


