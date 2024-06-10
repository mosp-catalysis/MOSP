import wx

class CharValidator(wx.Validator):
    def __init__(self, flag, infoBar=None, log=None):
        wx.Validator.__init__(self)
        self.LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.NUMS = '-0123456789.'
        self.POS_NUMS = '0123456789.'
        self.flag = flag
        self.infoBar = infoBar
        self.log = log
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return CharValidator(self.flag, self.infoBar, self.log)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()

        if self.flag == 'NUM_ONLY':
            for x in val:
                if x not in self.NUMS:
                    return False
        elif self.flag == 'POS_NUM_ONLY':
            for x in val:
                if x not in self.POS_NUMS:
                    return False
        elif self.flag == 'ALPHA_ONLY':
            for x in val:
                if x not in self.LETTERS:
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
