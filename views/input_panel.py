"""
@author: yinglei
"""

import wx
import wx.grid
try:
    import views.onoffbutton as oob
except:
    import onoffbutton as oob


class MyValidator(wx.Validator):
    def __init__(self, flag, infoBar):
        wx.Validator.__init__(self)
        self.LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.DIGITS = '-0123456789.'
        self.POS_DIGITS = '0123456789.'
        self.flag = flag
        self.infoBar = infoBar
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return MyValidator(self.flag, self.infoBar)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()

        if self.flag == 'ALPHA_ONLY':
            for x in val:
                if x not in self.LETTERS:
                    return False
        elif self.flag == 'DIGIT_ONLY':
            for x in val:
                if x not in self.DIGITS:
                    return False
        elif self.flag == 'POS_DIGIT ONLY':
            for x in val:
                if x not in self.POS_DIGITS:
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

        if self.flag == 'DIGIT_ONLY' and chr(key) in self.DIGITS:
            event.Skip()
            return
        
        if self.flag == 'POS_DIGIT ONLY' and chr(key) in self.POS_DIGITS:
            event.Skip()
            return

        if not wx.Validator.IsSilent():
            wx.Bell()
            if self.flag == 'POS_DIGIT ONLY':
                mes = 'Please enter positive number.'
            elif self.flag == 'DIGIT_ONLY':
                mes = 'Please enter digitals.'
            elif self.flag == 'ALPHA_ONLY':
                mes = 'Please enter letters.'
            if self.infoBar:
                self.infoBar.ShowMessage(mes, wx.ICON_INFORMATION)

        # Returning without calling even.Skip eats the event before it
        # gets to the text control
        return


class MsrPanel(wx.CollapsiblePane):
    def __init__(self, parent):
        wx.CollapsiblePane.__init__(self, parent, label='MSR', name='msr')
        self.win = self.GetPane()
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.win.SetSizerAndFit(self.Box)
        self.parent = parent
        # self.win.SetBackgroundColour('#f0f0f0')
        
        self.entries = {}
        self.__Init_GasesBox()
        self.__Init_FacesBox()

    def __Init_GasesBox(self):
        gasBox = wx.StaticBox(self.win, -1, 'Gases Info')
        gasBox.SetForegroundColour('#999')
        gasSizer = wx.StaticBoxSizer(gasBox, wx.VERTICAL)
        gasGridS = wx.FlexGridSizer(4, 5, 8, 16)
        gasSizer.Add(gasGridS, 0, wx.EXPAND|wx.ALL)
        self.Box.Add(gasSizer, 0, wx.EXPAND|wx.ALL)

        gasGridS.Add(wx.StaticText(self.win, label=''))
        gasGridS.Add(wx.StaticText(self.win, label='Name'), 0,  wx.ALIGN_CENTER_HORIZONTAL)
        gasGridS.Add(wx.StaticText(self.win, label='Partial Pressure (%)'), 0,  wx.ALIGN_CENTER_HORIZONTAL)
        gasGridS.Add(wx.StaticText(self.win, label='Gas Entropy (eV/K)'), 0,  wx.ALIGN_CENTER_HORIZONTAL)
        gasGridS.Add(wx.StaticText(self.win, label='Adsorption type'), 0,  wx.ALIGN_CENTER_HORIZONTAL)

        for i in range(1, 4):
            gasGridS.Add(wx.StaticText(self.win, label=f" Gas{i} "), 
                         0,  wx.ALIGN_CENTER_HORIZONTAL)
            for param in ['name', 'PP', 'S']:
                ety = wx.TextCtrl(self.win, -1, size=(120, -1), style=wx.TE_CENTRE)
                self.entries[f"Gas{i}_{param}"] = ety
                gasGridS.Add(ety, 0, wx.EXPAND)
                if param != 'name':
                    ety.SetValidator(MyValidator('POS_DIGIT ONLY', self.parent.infoBar))
            styles = ['Associative', 'Dissociative']
            combo = wx.ComboBox(self.win, -1, choices=styles, value=styles[0], 
                                size=(120, -1), style=wx.TE_CENTRE)
            self.entries[f"Gas{i}_type"] = combo
            gasGridS.Add(combo, 0, wx.EXPAND)

    def __Init_FacesBox(self):
        pass


class InputPanel(wx.ScrolledWindow):
    def __init__(self, parent, log):
        wx.ScrolledWindow.__init__(self, parent)
        self.log = log
        self.infoBar = wx.InfoBar(self)
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.Box)
        self.Box.Add(self.infoBar, 0, wx.EXPAND, 5)
        self.entries = {}
        self.__InitCommon()
        self.__InitOnoff()
        self.__InitMSR()
        self.__InitKMC()
    
    def __InitCommon(self):
        # dict-key, unit, type, combolist
        items = [("Element", '', 'Entry', ''),
                  ("Lattice constant", '(\u00C5)', 'Entry', 'POS_DIGIT ONLY'),
                  ("Crystal structure", '', 'Combobox', ('FCC', 'BCC')),
                  ("Pressure", '(Pa)', 'Entry', 'POS_DIGIT ONLY'), 
                  ("Temperature", '(K)', 'Entry', 'POS_DIGIT ONLY'),
                  ("Radius", '(\u00C5)', 'Entry', 'POS_DIGIT ONLY')]
        gridSz =  wx.FlexGridSizer(3, 6, 8, 16)
        for (label, unit, widget_type, dlc) in items:
            gridSz.Add(wx.StaticText(self, label=label+unit), 
                       0, wx.ALIGN_CENTER_HORIZONTAL)
            if widget_type == 'Entry':
                wgt = wx.TextCtrl(self, -1, size=(120, -1), style=wx.TE_CENTRE)
                wgt.SetValidator(MyValidator('POS_DIGIT ONLY', self.infoBar))
            elif widget_type == 'Combobox':
                wgt = wx.ComboBox(self, -1, choices=dlc, value=dlc[0], 
                                  size=(120, -1), style=wx.TE_CENTRE)
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
        boxh.Add(self.msrOnoff, 0, wx.ALL, 10)
        boxh.AddSpacer(10)
        boxh.Add(self.kmcOnoff, 0, wx.ALL, 10)
        self.Box.Add(boxh, 0, wx.ALL|wx.EXPAND)
        self.Bind(oob.EVT_ON, self.SwOn)
        self.Bind(oob.EVT_OFF, self.SwOff)
    
    def __InitMSR(self):
        self.msrPane = MsrPanel(self)
        self.msrPane.Collapse(False)
        self.Box.Add(self.msrPane, 0, wx.ALL|wx.EXPAND)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.SwColl)

    def __InitKMC(self):
        pass

    def SwOn(self, event):
        obj = event.GetEventObject()
        if obj.Name == 'msrOnoff':
            self.msrPane.Collapse(False)
        elif obj.Name == 'kmcOnoff':
            pass
    
    def SwOff(self, event):
        obj = event.GetEventObject()
        if obj.Name == 'msrOnoff':
            self.msrPane.Collapse(True)
        elif obj.Name == 'kmcOnoff':
            pass

    def SwColl(self, event):
        obj = event.GetEventObject()
        if obj.Name == 'msr':
            self.msrOnoff.Enable(self.msrPane.IsExpanded())
        elif obj.Name == 'kmc':
            pass



