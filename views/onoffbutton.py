'''
Author:     J Healey
Created:    14/01/2021
Copyright:  J Healey - 2021-2023
License:    GPL 3 or any later version
Version:    2.1.0
Email:      <rolfofsaxony@gmx.com>
Written & tested: Linux, Python 3.8.10
    Extensive testing on Windows by Ecco (Thank you for your patience)

    onoffbutton.py

    A custom class On/Off clickable - meant as a replacement for CheckBox.
     you may also toggle the control with the spacebar or clicking on the text.
     also offers you the ability to supply your own On and Off bitmaps

    Events: EVT_ON_OFF          Generic event on binary change

            EVT_ON              The control changed to On

            EVT_OFF             The control changed to Off

    Event Notes:
        All events return GetValue() and GetId() i.e.

            def OnOff(self, event):
                current_value = event.GetValue()
                id = event.GetId()

    Functions:
        GetValue()              Returns numeric value in the control On (True) = 1 Off (False) = 0
        SetValue(int)           Set numeric value in the control
        GetId()                 Get widget Id
        GetLabel()              Get current label for the control
        GetLabelText()          Get current label minus any mnemonic
        SetLabel(str)           Set label for the control
        SetToolTip(str)         Set tooltip for the control
        SetForegroundColour     Set text colour
        SetBackgroundColour     Set background colour
        SetOnColour             Set On background colour
        SetOnForegroundColour   Set On foreground colour
        SetOffColour            Set Off background colour
        SetOffForegroundColour  Set Off foreground colour
        SetOnOffColours(self, onback=None, onfore=None, offback=None, offfore=None)
                                Combines the 4 above functions
        SetFont(font)           Set label font
        GetFont()               Get label font
        Enable(Bool)            Enable/Disable the control
        IsEnabled()             Is the control Enabled - Returns True/False
        SetLabelTextColour      Override automatic label text colour selection
                                 Always perform this after setting On/Off colours
        GetFocusStyle()         Get the current pen style used to denote a widget with focus
        SetFocusStyle(style)    Set the pen style to use to denote a widget has focus.
                                 expects a valid wx.PenStyle
                                Defaults to wx.PENSTYLE_SOLID Suggestions: wx.PENSTYLE_DOT or
                                 wx.PENSTYLE_TRANSPARENT if you do not require Focus indicators
        SetBitmaps(on=None, off=None, focuson=None, focusoff=None)
                                Manually set an On bitmap and an Off bitmap
                                Optionally set On with Focus and Off with Focus bitmaps
                                 if these are omitted an attempt will be made to generate Focus images for you
                                All will be scaled to size
                                You may pass filenames, existing wx.Bitmaps or existing wx.Images
        SetBitmapSize(size)     Can be used in a 2 stage construction BEFORE adding bitmaps

    Default Values:
        initial - 0 (False) Off
        label   - blank
        style   - wx.TRANSPARENT_WINDOW|wx.BORDER_NONE
        mono    - False
        border  - True
        size    - 24x17 (Almost as small as a CheckBox)
        circle  - True
        internal_style - OOB_CIRCLE = 1
        rotate  - 0 (No rotation)

        The control is either a rounded rectangle or a rectangle, controlled by the parameter, circle
        The internal style indicator which shows the controls position, On or Off, can be a circle, an arrow
            a rectangle or a sized radio button, the default is a circle
            Choosing a rectangle forces the control to be a rectangular shape
            Choosing Radio forces the control to look like a radio button

        Label text colour is black or white based on the background colour, unless overriden
        Default background On  colour is '#32cd32' # lime green
        Default background Off colour is '#bfbfbf' # grey
        Tooltips are either [On] or [Off] unless a tooltip has been set, in which case [Currently On] or
         [Currently Off] is added to the existing tooltip

    Valid control styles:
        Window styles e.g. wx.BORDER_NONE, wx.BORDER_SIMPLE, wx.TRANSPARENT_WINDOW|wx.BORDER_SIMPLE etc
         if you override the default style wx.TRANSPARENT_WINDOW|wx.BORDER_NONE and you do not declare a
         background colour, remember to include wx.TRANSPARENT_WINDOW in your override or the control will
         default to a black background.

    Valid internal styles:
        OOB_CIRCLE          = 1 Default
        OOB_ARROW           = 2
        OOB_RECTANGLE       = 4
        OOB_SOFTRECTANGLE   = 8
        OOB_RADIO           = 16
        OOB_RADIOCHECK      = 32
        OOB_BULLET          = 64
        OOB_GRADIENT        = 128 (default On colour Green - default Off colour Red)

    Alignment internal styles:
        OOB_LEFT            = 1024 Default
        OOB_RIGHT           = 2048
        OOB_TOP             = 4096
        OOB_BOTTOM          = 8192

    An internal alignment style applies to the positioning of the control in relation to the text
    If the control is aligned OOB_TOP or OOB_BOTTOM, a second alignment flag OOB_LEFT or OOB_RIGHT
     can be applied which controls the alignment of the text below or above the control e.g.
        internal_style=OOB_ARROW|OOB_TOP|OOB_RIGHT
     By default it will be aligned centre.

'''

import wx

# Events OnOff, On and Off
oobEVT_ON_OFF = wx.NewEventType()
EVT_ON_OFF = wx.PyEventBinder(oobEVT_ON_OFF, 1)
oobEVT_ON = wx.NewEventType()
EVT_ON = wx.PyEventBinder(oobEVT_ON, 1)
oobEVT_OFF = wx.NewEventType()
EVT_OFF = wx.PyEventBinder(oobEVT_OFF, 1)

# Internal indicator styles
OOB_CIRCLE = 1
OOB_ARROW = 2
OOB_RECTANGLE = 4
OOB_SOFTRECTANGLE = 8
OOB_RADIO = 16
OOB_RADIOCHECK = 32
OOB_BULLET = 64
OOB_GRADIENT = 128
OOB_LEFT = 1024
OOB_RIGHT = 2048
OOB_TOP = 4096
OOB_BOTTOM = 8192

class OnOffEvent(wx.PyCommandEvent):
    """ Events sent from the :class:`OnOffButton` when the control changes.
        EVT_ON_OFF  The Control value has changed
        EVT_ON      The Control turned On
        EVT_OFF     The Control turned Off
    """

    def __init__(self, eventType, eventId=1, value=0):
        """
        Default class constructor.

        :param `eventType`: the event type;
        :param `eventId`: the event identifier.
        """

        wx.PyCommandEvent.__init__(self, eventType, eventId)
        self._eventType = eventType
        self.value = value

    def GetValue(self):
        """
        Retrieve the value of the control at the time
        this event was generated.
        """
        return self.value


class OnOffButton(wx.Control):

    def __init__(self, parent, id=wx.ID_ANY, label="", pos=wx.DefaultPosition, size=wx.DefaultSize, initial=0,\
                 style=wx.TRANSPARENT_WINDOW|wx.BORDER_NONE, mono=False, border=True, circle=True, \
                 internal_style=OOB_CIRCLE, rotate=0, name="OnOff_Button"):
        """
        Default class constructor.

        @param parent:  Parent window. Must not be None.
        @param id:      identifier. A value of -1 indicates a default value.
        @param label:   control label.
        @param pos:     Position. If the position (-1, -1) is specified
                        then a default position is chosen.
        @param size:    If the default size (-1, -1) is specified then the minimum size is chosen.
        @param initial: Initial value 0 False or 1 True
                        - default False.
        @param style:   wx.Border style default wx.TRANSPARENT_WINDOW|wx.BORDER_NONE
        @param mono:    True or False makes the image monochrome
                        - default False
        @param border:  True or False adds a border to the controls image
                        - default True
        @param circle:  True or False Control is a Rounded Rectangle or a Standard Rectangle
                        - When used with a RADIO style the radio button is Circular or Square
                        - default True
        @param internal_style:   The style of On/Off indicator
                        - default 0 (Circle)
        @param rotate   0 = No rotation | 1 = 90° clockwise | 2 = 180° | <0 = 90° anti-clockwise
        @param name:    Widget name.
        """

        # Quirk in wx.CONTROL__init__() adds a wx.BORDER_DOUBLE, if wx.ALIGN_RIGHT has been set, don't know why
        # So unless a border has been specifically requested we default to None
        #if style == wx.ALIGN_RIGHT:
        #    style = wx.ALIGN_RIGHT | wx.BORDER_NONE
        # resolved by moving alignment to an internal parameter

        wx.Control.__init__(self, parent, id, pos=pos, size=size, style=style, name=name)

        self._initial = initial
        self._label = label
        self._pos = pos
        self._size = size
        self._name = name
        self._mono = mono
        self._border = border
        self._style = style
        self._circle = circle
        self._rotate = rotate
        self._internal_style = internal_style
        # Test internal_style for a valid shape style
        if self._internal_style & OOB_CIRCLE or self._internal_style & OOB_ARROW or \
            self._internal_style & OOB_RECTANGLE or self._internal_style & OOB_SOFTRECTANGLE or \
            self._internal_style & OOB_RADIO or self._internal_style & OOB_RADIOCHECK or \
            self._internal_style & OOB_BULLET or self._internal_style & OOB_GRADIENT:
            pass
        else:
            self._internal_style = self._internal_style | OOB_CIRCLE
        if self._internal_style & OOB_RECTANGLE:
            self._circle = False
        if self._internal_style & OOB_SOFTRECTANGLE:
            self._circle = False
        if self._internal_style & OOB_GRADIENT:
            self._circle = False
        self.OnClr = '#32cd32' # lime green
        self.OffClr = '#bfbfbf' # grey
        self.OnClrForeground = None
        self.OffClrForeground = None
        self.own_txt_colour = None
        self.mnemonic = False
        self.onbit = self.offbit = self.focusonbit = self.focusoffbit = None
        self._font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        if self._mono:
            self.OnClr = self.OffClr = '#ffffff' # white
        if self._mono and self._internal_style & OOB_GRADIENT:
            self.OnClr = "#000000"
            self.OffClr = "#ffffff"
        elif self._internal_style & OOB_GRADIENT:
            self.OnClr = "#00ff00"
            self.OffClr = "#ff0000"
        if self._internal_style & OOB_RADIO or self._internal_style & OOB_RADIOCHECK:
            self.OffClr = '#ffffff' # white
        if self._initial > 1:
            self._initial = 1
        if self._initial < 0:
            self._initial = 0
        self._Value = initial
        self._focus_style = wx.PENSTYLE_SOLID
        self._backgroundcolour = parent.GetBackgroundColour()
        self._foregroundcolour = parent.GetForegroundColour()

        # Initialize images
        self.InitialiseBitmaps()
        self.onoff = wx.StaticBitmap(self, -1, bitmap=wx.Bitmap(self._img))
        self.label = wx.StaticText(self, -1, self._label)
        self.mnemonic = self.Mnemonic(self._label)

        # Bind the event
        self.onoff.Bind(wx.EVT_LEFT_DOWN, self.OnOff)
        self.label.Bind(wx.EVT_LEFT_DOWN, self.OnOff)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

        if self._internal_style & OOB_TOP or self._internal_style & OOB_BOTTOM:
            # For control placed top or bottom check for an extra alignment Left/Right flag
            algn =  wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP
            if self._internal_style & OOB_LEFT:
                algn = wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP
            if self._internal_style & OOB_RIGHT:
                algn = wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT|wx.TOP
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            if self._internal_style & OOB_BOTTOM:
                self.sizer.Add(self.label, 0, algn, 5)
                self.sizer.Add(self.onoff, 0, algn, 5)
            else:
                self.sizer.Add(self.onoff, 0, algn, 5)
                self.sizer.Add(self.label, 0, algn, 5)
        else:
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)
            if self._internal_style & OOB_RIGHT:
                self.sizer.Add(self.label, 0, wx.ALIGN_CENTER|wx.LEFT, 5)
                self.sizer.Add(self.onoff, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT, 5)
            else:
                self.sizer.Add(self.onoff, 0, wx.ALIGN_CENTER|wx.LEFT, 5)
                self.sizer.Add(self.label, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT, 5)
        if not self._label:
            self.sizer.Hide(self.label)
        self.SetImage(self._initial)
        self.SetSizerAndFit(self.sizer)
        self.Layout()

        if wx.Platform == '__WXMSW__':
            self.SetBackgroundColour(self._backgroundcolour)
        _colour = self.GetBackgroundColour()
        txt_colour, brightness = self.GetBrightness(self._backgroundcolour)
        self.SetForegroundColour(txt_colour)

        if self._label:
            self.SetLabel(self._label)
#            self.SetFocus()

    def InitialiseBitmaps(self):
        self._bitmaps = {
            "FocusOn": self._CreateBitmap("FocusOn"),
            "FocusOff": self._CreateBitmap("FocusOff"),
            "On": self._CreateBitmap("On"),
            "Off": self._CreateBitmap("Off"),
            "DisableOff": self._CreateBitmap("DisableOff"),
            "DisableOn": self._CreateBitmap("DisableOn"),
            }

        if self._initial <= 0:
            self._img = self._bitmaps['Off']
        elif self._initial >= 1:
            self._img = self._bitmaps['On']

    def _CreateBitmap(self, type):
        if type == "FocusOn":   # The tallest bitmap
            self.SetImageSize()
        bmp = wx.Bitmap.FromRGBA(self.bmpw, self.bmph, red=255, green=255, blue=255, alpha=0)
        dc = wx.MemoryDC(bmp)
        try:
            gcdc = wx.GCDC(dc) # Anti-aliased for Windows ?? Who knows? Not me!
        except Exception as e:
            gcdc = dc

        bg = self.GetBackgroundColour()
        edge_colour, brightness = self.GetBrightness(bg)

        # On/Off bitmaps supplied - Use those
        if self.onbit and self.offbit: # use manually supplied bitmaps
            bmp, result = self._UseSuppliedBitmap(type, dc, edge_colour)
            if result: # Successful
                del dc, gcdc
                return bmp

        fg = self.GetForegroundColour()
        if self.OnClrForeground is None:
            self.OnClrForeground = '#000000' # Black
        if self.OffClrForeground is None:
            self.OffClrForeground = '#000000' # Black
        brush = wx.Brush(bg)
        if self._style & wx.TRANSPARENT_WINDOW:
            brush = wx.Brush("#ffffff", style=wx.BRUSHSTYLE_TRANSPARENT)
        gcdc.SetBackground(brush)
        gcdc.Clear()

        gcdc.SetBrush(wx.Brush("#ffffff"))
        gcdc.SetPen(wx.Pen(edge_colour, 1))

        # Outer Shape -------------------------------------------- #

        if self._circle:
            if self._border:
                gcdc.DrawRoundedRectangle(self.rrouterposx, self.rrouterposy, self.rrouterw, self.rrouterh, \
                                          self.rrouterradius)
            if "On" in type:
                gcdc.SetBrush(wx.Brush(self.OnClr))
            elif "Off" in type:
                gcdc.SetBrush(wx.Brush(self.OffClr))
            else:
                gcdc.SetBrush(wx.Brush('#bfbfbf'))
            if "Disable" in type or self._mono:
                gcdc.SetBrush(wx.Brush('#ffffff')) # white
            gcdc.SetPen(wx.Pen("#ffffff"))
            gcdc.DrawRoundedRectangle(self.rrinnerposx, self.rrinnerposy, self.rrinnerw, self.rrinnerh, \
                                      self.rrinnerradius)
            if "Focus" in type:
                #gcdc.SetBrush(wx.Brush(wx.NullBrush))
                gcdc.SetBrush(wx.Brush(wx.Colour(255, 255, 255, wx.ALPHA_TRANSPARENT), wx.BRUSHSTYLE_TRANSPARENT))
                gcdc.SetPen(wx.Pen(edge_colour, width=1, style=self._focus_style))
                gcdc.DrawRoundedRectangle(self.rrouterposx-3, self.rrouterposy-3, self.rrouterw+6, \
                                          self.rrouterh+6, 4)
        else:
            corner = 0
            if self._internal_style & OOB_SOFTRECTANGLE:
                corner = 4
            if self._border:
                gcdc.DrawRoundedRectangle(self.rrouterposx, self.rrouterposy, self.rrouterw, self.rrouterh, \
                                          corner)
            if "On" in type:
                gcdc.SetBrush(wx.Brush(self.OnClr))
            elif "Off" in type:
                gcdc.SetBrush(wx.Brush(self.OffClr))
            if "Disable" in type:
                gcdc.SetBrush(wx.Brush('#bfbfbf')) # grey
            if type[:7] == "Disable" or self._mono:
                gcdc.SetBrush(wx.Brush('#ffffff')) # white/grey
            gcdc.SetPen(wx.Pen("#ffffff", width=1, style=wx.PENSTYLE_SOLID))
            gcdc.DrawRoundedRectangle(self.rrinnerposx, self.rrinnerposy, self.rrinnerw, self.rrinnerh, \
                                      corner)
            if "Focus" in type:
                corner = 4
                #if not OOB_SOFTRECTANGLE & self._internal_style: # rectangular focus on rectangular widget ??
                #    corner = 0
                #gcdc.SetBrush(wx.Brush(wx.NullBrush))
                gcdc.SetBrush(wx.Brush(wx.Colour(255, 255, 255, wx.ALPHA_TRANSPARENT), wx.BRUSHSTYLE_TRANSPARENT))
                gcdc.SetPen(wx.Pen(edge_colour, width=1, style=self._focus_style))
                gcdc.DrawRoundedRectangle(self.rrouterposx-3, self.rrouterposy-3, self.rrouterw+6, \
                                          self.rrouterh+6, corner)

        onedge_colour, brightness = self.GetBrightness(self.OnClrForeground)
        offedge_colour, brightness = self.GetBrightness(self.OffClrForeground)

        # Inner Shape -------------------------------------------- #

        if "On" in type:
            corner = 0
            gcdc.SetPen(wx.Pen(onedge_colour, width=1, style=wx.PENSTYLE_SOLID))
            if self._internal_style & OOB_SOFTRECTANGLE:
                corner = 4
            gcdc.SetBrush(wx.Brush(self.OnClrForeground))

            if type == "DisableOn":
                gcdc.SetBrush(wx.Brush('#484848')) # grey

            if self._internal_style & OOB_ARROW:
                gcdc.DrawPolygon([(self.rrouterw+1, int(self.rrouterh/2)+3),
                                  (int(self.rrouterw/2)+3,4),
                                  (int(self.rrouterw/2)+3,self.rrouterh+1)],
                                   0,0)

            elif self._internal_style == OOB_RECTANGLE or self._internal_style == OOB_SOFTRECTANGLE:
                x = self.rrinnerposx+int(self.rrouterw/2) - 2
                y = self.rrinnerposy
                w = int(self.rrinnerw/2)+1
                h = self.rrinnerh
                gcdc.DrawRoundedRectangle(x, y, w, h, corner)

            elif self._internal_style & OOB_BULLET:
                gcdc.SetPen(wx.Pen(edge_colour, width=1, style=wx.PENSTYLE_SOLID))
                gcdc.DrawArc((int(self.circonpos[0]), int(self.circonpos[1]+self.rrinnerh/2)+2),
                             (int(self.circonpos[0]), int(self.circonpos[1]-self.rrinnerh/2)+2),
                             (int(self.circonpos[0]), int(self.circonpos[1])))
                if type != "DisableOn":
                    gcdc.SetPen(wx.Pen(self.OnClrForeground, width=1, style=wx.PENSTYLE_SOLID))
                else:
                    gcdc.SetPen(wx.Pen('#484848')) # grey
                x = self.rrinnerposx+int(self.rrouterw/2) -2
                y = self.rrinnerposy+1
                w = int(self.rrinnerw/4)
                h = self.rrinnerh-2
                gcdc.DrawRoundedRectangle(x, y, w, h, corner)
                if type != "DisableOn":
                    gcdc.SetBrush(wx.Brush(self.OnClr))
                else:
                    gcdc.SetBrush(wx.Brush('#bfbfbf')) # grey
                _x, _y = divmod(self.circradius, 2)
                lc = _x + _y # always round up radius/2
                lc = max(lc,3)
                gcdc.DrawCircle(int(self.circonpos[0]+(lc/2)), int(self.circonpos[1]), lc)

            elif self._internal_style & OOB_GRADIENT:
                gcdc.GradientFillLinear((self.rrinnerposx, self.rrinnerposy, self.rrinnerw, self.rrinnerh),\
                                        self.OffClr, self.OnClr, wx.RIGHT)

            elif self._internal_style & OOB_RADIO and self._circle:
                gcdc.DrawCircle(int(self.circoffpos[0]), int(self.circoffpos[1]), int(self.circradius))

            elif self._internal_style & OOB_RADIOCHECK and self._circle:
                gcdc.DrawCheckMark(self.rrinnerposx, self.rrinnerposy, self.rrinnerw, self.rrinnerh)

            elif self._internal_style & OOB_RADIO:
                gcdc.DrawRectangle(self.rrinnerposx, self.rrinnerposy, self.rrinnerw, self.rrinnerh)

            elif self._internal_style & OOB_RADIOCHECK:
                gcdc.DrawCheckMark(self.rrinnerposx, self.rrinnerposy, self.rrinnerw, self.rrinnerh)

            else:
                gcdc.DrawCircle(int(self.circonpos[0]), int(self.circonpos[1]), int(self.circradius)-1)

        else:
            corner = 0
            gcdc.SetPen(wx.Pen(offedge_colour, width=1, style=wx.PENSTYLE_SOLID))
            if self._internal_style & OOB_SOFTRECTANGLE:
                corner = 4
            gcdc.SetBrush(wx.Brush(self.OffClrForeground))
            if type == "DisableOff":
                gcdc.SetBrush(wx.Brush('#484848')) # grey

            if self._internal_style & OOB_ARROW:
                gcdc.DrawPolygon([(4, int(self.rrouterh/2)+3),
                                  (int(self.rrouterw/2)+3,4),
                                  (int(self.rrouterw/2)+3,self.rrouterh+1)],
                                   0,0)

            elif self._internal_style == OOB_RECTANGLE or self._internal_style == OOB_SOFTRECTANGLE:
                x = self.rrinnerposx
                y = self.rrinnerposy
                w = int(self.rrinnerw/2)+1
                h = self.rrinnerh
                gcdc.DrawRoundedRectangle(x, y, w, h, corner)

            elif self._internal_style & OOB_BULLET:
                gcdc.SetPen(wx.Pen(edge_colour, width=1, style=wx.PENSTYLE_SOLID))
                gcdc.DrawArc((int(self.circoffpos[0]), int(self.circoffpos[1]-self.rrinnerh/2)-1),
                             (int(self.circoffpos[0]), int(self.circoffpos[1]+self.rrinnerh/2)-1),
                             (int(self.circoffpos[0]), int(self.circoffpos[1])))
                if type != "DisableOff":
                    gcdc.SetPen(wx.Pen(self.OffClrForeground, width=1, style=wx.PENSTYLE_SOLID))
                else:
                    gcdc.SetPen(wx.Pen('#484848')) # grey
                x = self.rrinnerposx+int(self.rrinnerw/4) +1
                y = self.rrinnerposy+1
                w = int(self.rrinnerw/4)
                h = self.rrinnerh-2
                gcdc.DrawRoundedRectangle(x, y, w, h, corner)

            elif self._internal_style & OOB_GRADIENT:
                gcdc.GradientFillLinear((self.rrinnerposx, self.rrinnerposy, self.rrinnerw, self.rrinnerh),\
                                        self.OffClr, self.OnClr, wx.LEFT)

            elif self._internal_style & OOB_RADIO and self._circle:
                pass
                #gcdc.DrawCircle(int(self.circoffpos[0]), int(self.circoffpos[1]), int(0))

            elif self._internal_style & OOB_RADIOCHECK:
                pass

            elif self._internal_style & OOB_RADIO:
                gcdc.DrawRectangle(self.rrinnerposx +1, self.rrinnerposy +1, 0, 0)

            elif self._internal_style & OOB_RADIOCHECK:
                gcdc.DrawRectangle(self.rrinnerposx +1, self.rrinnerposy +1, 0, 0)

            else:
                gcdc.DrawCircle(int(self.circoffpos[0]), int(self.circoffpos[1]), int(self.circradius)-1)

        #Test draw alignment centre lines
        #gcdc.DrawLine(0, int((self.bmph-1)/2), self.bmpw,int((self.bmph-1)/2))
        #gcdc.DrawLine(int((self.bmpw-1)/2), 0, int((self.bmpw-1)/2),int((self.bmph)))

        bmp = dc.GetAsBitmap((0, 0, self.bmpw, self.bmph))
        if self._rotate:
            if self._rotate > 0:
                direction = True
            else:
                direction = False
            img = bmp.ConvertToImage()
            if self._rotate != 2:
                img = img.Rotate90(direction)
            else:
                img = img.Rotate180()
            bmp = img.ConvertToBitmap(depth=32)

        del dc, gcdc
        return bmp

    def _UseSuppliedBitmap(self, type, dc, edge_colour):
        if "On" in type:
            if type == "FocusOn":
                onbit = self.focusonbit
            else:
                onbit = self.onbit
            if isinstance(onbit, str):
                img = wx.Image(onbit, type=wx.BITMAP_TYPE_ANY) # file
            elif isinstance(onbit, wx.Bitmap):
                img = onbit.ConvertToImage() # existing bitmap
            elif isinstance(onbit, wx.Image):
                img = onbit
            else: # error
                img = ''
        else:
            if type == "FocusOff":
                offbit = self.focusoffbit
            else:
                offbit = self.offbit
            if isinstance(offbit, str):
                img = wx.Image(offbit, type=wx.BITMAP_TYPE_ANY) # file
            elif isinstance(offbit, wx.Bitmap):
                img = offbit.ConvertToImage() # existing bitmap
            elif isinstance(offbit, wx.Image):
                img = offbit
            else: # error
                img = ''

        # Test for supplied focus bitmaps - if None rescale smaller to allow for focus indicator to be added
        # If focus bitmaps exist rescale without allowing for added border
        if self.focusonbit == self.onbit and self.focusoffbit == self.offbit:
            rescale_width = self.bmpw-7
            rescale_height = self.bmph-6
            posx = 3
            posy = 3
        else:
            rescale_width = self.bmpw
            rescale_height = self.bmph
            posx = 0
            posy = 0
        try:
            img.Rescale(rescale_width, rescale_height, quality=wx.IMAGE_QUALITY_HIGH)
        except Exception:
            # something has failed - return False and default to a generated image
            return None, False

        bmp = img.ConvertToBitmap(depth=32)
        bmp.UseAlpha()
        dc.DrawBitmap(bmp, posx, posy)

        # If no supplied focus bitmaps - we need to add a focus indicator border
        if self.focusonbit == self.onbit and self.focusoffbit == self.offbit :
            if "Focus" in type:
                r, g, b, a = self._backgroundcolour.Get()
                if wx.Platform == '__WXMSW__': # Windows refuses to draw non-transparent rectangle outside of image
                                               # so recreate dc with normal background colour
                    fbmp = wx.Bitmap.FromRGBA(self.bmpw, self.bmph, r, g, b, 0)
                    dc.SetBackground(wx.Brush(self._backgroundcolour))
                    dc.Clear()
                dc.SetBrush(wx.Brush(self._backgroundcolour, wx.BRUSHSTYLE_TRANSPARENT))
                dc.SetPen(wx.Pen(edge_colour, width=1, style=self._focus_style))
                dc.DrawBitmap(bmp, posx, posy)
                dc.DrawRoundedRectangle(self.rrouterposx-3, self.rrouterposy-3, self.rrouterw+6, self.rrouterh+6, 4)

        bmp = dc.GetAsBitmap((0, 0, self.bmpw, self.bmph))

        if self._rotate:
            if self._rotate > 0:
                direction = True
            else:
                direction = False
            img = bmp.ConvertToImage()
            if self._rotate != 2:
                img = img.Rotate90(direction)
            else:
                img = img.Rotate180()
            bmp = img.ConvertToBitmap(depth=32)

        if "Disable" in type:
            bmp = self.DisableImage(bmp)

        # testing
        #bmp.SaveFile(type+'.png', wx.BITMAP_TYPE_PNG)

        return bmp, True

    def DisableImage(self, bmp):
        bmp = bmp.ConvertToDisabled()
        bmp.UseAlpha()
        return bmp

    def SetImageSize(self):
        w, h = self._size
        # Cater for only Width or only Height parameter given
        ratio = 0.6667 # fixed rectangular ratio
        if self.onbit:
            bitw, bith = wx.Bitmap(self.onbit).GetSize()
            ratio = bith / bitw # ratio for supplied image
        if h < 0 and w >= 0:
            h = int(w * ratio)
        if w < 0 and h >= 0:
            w = int(h / ratio)
        # Set Default minimum size or stated size, also caters for no size set (-1, -1)
        if self._internal_style & OOB_RADIO or self._internal_style & OOB_RADIOCHECK:
            w = max(self._size[0], 16)
            h = max(self._size[1], 16)
        else:
            w = max(w, 24)
            h = max(h, 17)

        if self._internal_style & OOB_RADIO or self._internal_style & OOB_RADIOCHECK: # force equal dimensions for radio
            m = max(w, h)
            if not m % 2: # Odd number centres properly
                m -= 1
            w = h = m
        # Ensure w % h are integers and odd
        w = int(w)
        h = int(h)
        if not h % 2:
            h -= 1
        if not w % 2:
            w -= 1

        # Outer rounded rectangle
        self.rrouterw = w - 2
        self.rrouterh = h - 2
        self.rrouterposx = 3
        self.rrouterposy = 3
        self.rrouterradius = int(self.rrouterh/2)
        # Inner rounded rectangle
        self.rrinnerw = self.rrouterw - 4
        self.rrinnerh = self.rrouterh - 4
        self.rrinnerposx = self.rrouterposx + 2
        self.rrinnerposy = self.rrouterposy + 2
        self.rrinnerradius = int(self.rrinnerh/2)
        # Circle position and size
        self.circradius = round(self.rrinnerradius)
        if self._internal_style & OOB_CIRCLE:
            if self.circradius >= 8:
                self.circradius += 2
            else:
                self.circradius += 1
        else: # if circle adjust radius for a fractional overlap
            pass
        self.circoffpos = (round(self.rrinnerradius+self.rrinnerposx), round(self.rrinnerposy + self.rrinnerradius))
        self.circonpos = (round(self.rrinnerw - (self.rrinnerradius-4)), round(self.rrinnerposy + self.rrinnerradius))

        # allow border for focus indicator
        self.bmpw = w+5
        self.bmph = h+4

    def SetValue(self, value):
        if value:
            if value > 1:
                value = 1
            if value < 0:
                value = 0
            self._Value = value
            self.SetImage(value)
            self.Update()

    def GetValue(self):
        if self._Value:
            return True
        else:
            return False

    def SetLabel(self, label):
        self.label.SetLabel(label)
        font = self._font
        if not font.IsOk(): # Invalid font - swap out for the system default
            font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        dc = wx.MemoryDC()
        dc.SetFont(font)
        textW, textH = dc.GetTextExtent(label)
        if wx.Platform == '__WXMSW__':
            # Windows wx.StaticText appears to cater for font size changes
            pass
        else:
            # GTK3 Linux doesn't - MacOs ??????
            # Bug https://github.com/wxWidgets/Phoenix/issues/1228
            # Bug https://github.com/wxWidgets/wxWidgets/issues/16088
            self.label.SetMinSize(wx.Size(textW, textH))
        bs = self.DoGetBestSize()
        bs.SetHeight(bs.Height+10)
        self.SetMinSize(bs)
        self.mnemonic = self.Mnemonic(label)
        self._label = label
        _colour = self.GetBackgroundColour()
        self.txt_colour, brightness = self.GetBrightness(_colour)
        self.label.SetForegroundColour(self.txt_colour)

        if label:
            self.sizer.Show(self.label)
        self.Refresh()

    def GetBrightness(self, _colour):
        '''
        Set text colour based on the brightness of the current background colour
        Override with SetLabelTextColour
        '''
        try: # requires wxpython 4.1 widgets 3.1.3
            brightness = wx.Colour(_colour).GetLuminance()
        except Exception as e:
            try:
                red = wx.Colour.Red(_colour)
                green = wx.Colour.Green(_colour)
                blue = wx.Colour.Blue(_colour)
                brightness = ( 0.299*red + 0.587*green + 0.114*blue )
            except Exception:
                brightness = 127
            brightness = brightness / 255

        if brightness < 0.5:
            txt_colour = wx.WHITE
        else:
            txt_colour = wx.BLACK
        if self.own_txt_colour:
            txt_colour = self.own_txt_colour
        return txt_colour, brightness

    def Mnemonic(self, label):
        mnemonic = label
        if "&&" in mnemonic: # remove literal & from the test
            mnemonic = mnemonic.replace('&&', '')
        if "&" in mnemonic: # find first &
            st, *end = mnemonic.split('&', 1)
            char = end[0][0]
            return ord(char.upper())
        else:
            return False

    def OnKey(self, event):
        keycode = event.GetKeyCode()
        if event.GetModifiers() == wx.MOD_ALT and keycode == self.mnemonic: # Alt + & marked label character
            self.OnOff(None)
        elif keycode == wx.WXK_SPACE:
                self.OnOff(None)
        elif keycode == wx.WXK_ALT: # Find focus and toggle to identify
            obj = self.FindFocus()
            if obj:
                obj.Navigate()
                obj.SetFocus()
        else:
            event.Skip(True)

    def GetLabel(self):
        return self.label.GetLabel()

    def GetLabelText(self):
        label = self.label.GetLabel()
        label = label.replace('&&', '¿¿')
        label = label.replace('&', '', 1)
        label = label.replace('¿¿', '&')
        return label

    def IsEnabled(self):
        return wx.Control.IsEnabled(self)

    def Disable(self, value=True):
        self.Enable(not value)

    def Enable(self, value=True):
        if self.HasFocus(): # disabling focused item - attempt to pass focus
            obj = self.GetNextSibling()
            if not obj or type(obj).__name__ != "OnOffButton" or not obj.IsEnabled():
                obj = self.GetPrevSibling()
            if obj and type(obj).__name__ == "OnOffButton" and obj.IsEnabled():
                obj.SetFocus()
        wx.Control.Enable(self, value)
        self.SetImage(self.GetValue())
        if self.IsEnabled(): # force text change
            self.label.SetForegroundColour(self.txt_colour)
        else:
            self.label.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
        self.Refresh()

    def SetToolTip(self, tip):
        wx.Control.SetToolTip(self, tip)
        self.Refresh()

    def SetHelpText(self, text):
        wx.Control.SetHelpText(self, text)
        self.onoff.SetHelpText(text)
        self.Refresh()

    def ShouldInheritColours(self):
        return True

    def SetForegroundColour(self, colour):
        wx.Control.SetForegroundColour(self, colour)
        self.InitialiseBitmaps()
        self.SetImage(self._Value)
        self.Refresh()

    def SetBackgroundColour(self, colour):
        wx.Control.SetBackgroundColour(self, colour)
        self.InitialiseBitmaps()
        self.SetImage(self._Value)
        self.txt_colour, brightness = self.GetBrightness(colour)
        self.label.SetForegroundColour(self.txt_colour)
        self.Refresh()

    def SetLabelTextColour(self, colour):
        self.label.SetForegroundColour(colour)
        self.own_txt_colour = colour
        self.Refresh()

    def SetOnOffColours(self, onback=None, onfore=None, offback=None, offfore=None):
        if onback:
            self.OnClr = onback
        if onfore:
            self.OnClrForeground = onfore
        if offback:
            self.OffClr = offback
        if offfore:
            self.OffClrForeground = offfore
        self.InitialiseBitmaps()
        self.SetImage(self._Value)
        self.Refresh()

    def SetOnColour(self, colour):
        self.OnClr = colour
        self.InitialiseBitmaps()
        self.SetImage(self._Value)
        self.Refresh()

    def SetOnForegroundColour(self, colour):
        self.OnClrForeground = colour
        self.InitialiseBitmaps()
        self.SetImage(self._Value)
        self.Refresh()

    def SetOffColour(self, colour):
        self.OffClr = colour
        self.InitialiseBitmaps()
        self.SetImage(self._Value)
        self.Refresh()

    def SetOffForegroundColour(self, colour):
        self.OffClrForeground = colour
        self.InitialiseBitmaps()
        self.SetImage(self._Value)
        self.Refresh()

    def SetFont(self, font):
        wx.Control.SetFont(self, font)
        self.label.SetFont(font)
        self._font = font
        # Font changed reset label
        self.SetLabel(self._label)

    def GetFont(self):
        return self._font

    def GetFocusStyle(self):
        return self._focus_style

    def SetFocusStyle(self, style):
        self._focus_style = style
        self._bitmaps["FocusOn"] = self._CreateBitmap("FocusOn")
        self._bitmaps["FocusOff"] = self._CreateBitmap("FocusOff")

    def OnOff(self, event):
        state = self._Value
        if state == 0:
            state = 1
        else:
            state = 0

        self.SetImage(state)
        self.SetValue(state)
        self.SetFocus()
        # event change
        event = OnOffEvent(oobEVT_ON_OFF, self.GetId(), state)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)
        if state:
            # event On
            event = OnOffEvent(oobEVT_ON, self.GetId(), state)
            event.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(event)
        else:
            # event Off
            event = OnOffEvent(oobEVT_OFF, self.GetId(), state)
            event.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(event)

    def SetImage(self, value):
        # Set appropriate image and tooltip
        tp = self.GetToolTip()
        if self.IsEnabled():
            if value <= 0:
                self._img = self._bitmaps['Off']
                self.SetFont(self._font)
                if tp is not None:
                    tt = tp.GetTip()+"\n[ Off ]"
                else:
                    tt = "[ Off ]"
            else:
                self._img = self._bitmaps['On']
                self.SetFont(self._font)
                if tp is not None:
                    tt = tp.GetTip()+"\n[ On ]"
                else:
                    tt = "[ On ]"
        else: # Disabled
            if value <= 0:
                self._img = self._bitmaps['DisableOff']
            else:
                self._img = self._bitmaps['DisableOn']
            if tp is not None:
                tt = tp.GetTip()+"\n[ Disabled ]"
            else:
                tt = "[ Disabled ]"

        if hasattr(self, 'onoff'): # Not present if initially setting the parent backgroundcolour
            self.onoff.SetBitmap(wx.Bitmap(self._img))
            self.onoff.SetToolTip(tt)

    def SetBitmaps(self, on=None, off=None, focuson=None, focusoff=None):
        if on and off:
            pass
        else:
            return
        self.onbit = on
        if focuson:
            self.focusonbit = focuson
        else: # if focuson missing assign copy of On bitmap
            self.focusonbit = on
        self.offbit = off
        if focusoff:
            self.focusoffbit = focusoff
        else: # if focusoff missing assign copy of Off bitmap
            self.focusoffbit = off
        self.InitialiseBitmaps()
        self.SetImage(self._Value)
        self.Refresh()

    def OnFocus(self, event):
        if self._Value:
            img = self._bitmaps['FocusOn']
        else:
            img = self._bitmaps['FocusOff']
        self.onoff.SetBitmap(wx.Bitmap(img))
        #event.Skip()
        return

    def OnKillFocus(self, event):
        if self._Value:
            img = self._bitmaps['On']
        else:
            img = self._bitmaps['Off']
        self.onoff.SetBitmap(wx.Bitmap(img))
        #event.Skip()
        return

    def SetBitmapSize(self, size):
        # can be used in a 2 stage construction BEFORE adding bitmaps which are sized
        # differently from the original definition - Minimum width 24 height 17
        # size should be wx.Size(x, y) or a tuple (x, y)
        self._size = size
