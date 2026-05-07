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
from utils.kmc_oi import writeEkmcInp

try:
    import views.onoffbutton as oob
    from views.validator import CharValidator
    from views.dataclass import Specie, Product, Event
    from views.input_panel import LiPane
    from views.input_panel import SpeciePane, popupAdsDesInSpe
    from views.input_panel import GET_FONT, GET_INFO_BMP
    from views.particle import NanoParticle
except:
    import onoffbutton as oob
    from validator import CharValidator
    from dataclass import Specie, Product, Event
    from input_panel import LiPane
    from input_panel import SpeciePane, popupAdsDesInSpe
    from input_panel import GET_FONT, GET_INFO_BMP
    from particle import NanoParticle

BG_COLOR = 'white'
POP_BG_COLOR = '#FFFAEF'
WARNING_COLOR = '#D6B4FD'
FIX_COLOR = '#B0C4DE'

class InputPanelEKMC(wx.ScrolledWindow):
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
        self.__InitRunButton()
        self.__InitEKMC()
    
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
                if label != 'Element':
                    wgt.SetValidator(self.posDigitValidator)
            elif widget_type == 'Combobox':
                wgt = wx.ComboBox(self, -1, choices=dlc, value=dlc[0], 
                                  size=(120, -1), style=wx.CB_READONLY|wx.TE_CENTER)
            gridSz.Add(wgt, 0, wx.ALIGN_CENTER)
            self.entries[label] = wgt

        self.Box.AddSpacer(8)
        self.Box.Add(gridSz, 0, wx.EXPAND, 5)
    
    def __InitRunButton(self):
        boxh = wx.BoxSizer(wx.HORIZONTAL)

        self.ekmcRunBtn = wx.Button(self, -1, "Run EKMC")
        self.ekmcRunBtn.Bind(wx.EVT_BUTTON, self.OnRunEKMC)
        boxh.Add(self.ekmcRunBtn, 0, wx.ALL, 8)

        self.Box.Add(boxh, 0, wx.ALL|wx.EXPAND)

    def __InitEKMC(self):
        self.ekmcPane = EkmcPanel(self)
        self.Box.Add(self.ekmcPane, 0, wx.ALL|wx.EXPAND)

    def __getwildcard(self):
        return  ("JSON files (*.json)|*.json|"
                 "Text files (*.txt)|*.txt|"
                 "All files (*.*)|*.*")
        
    def __save(self):
        for key, widget in self.entries.items():
            self.values[key] = widget.GetValue()
        self.values['EKMC'] = self.ekmcPane.OnSave()

    def get_values(self):
        self.__save()
        return self.values

    def set_values(self, values):
        for key, widget in self.entries.items():
            if (values.get(key) != None):
                widget.SetValue(values[key])
        if values.get('EKMC'):
            self.ekmcPane.OnLoad(values['EKMC'])
        self.OnInnerSizeChanged()

    def OnSave(self):
        # print('Save EKMC inputs ...')
        values = self.get_values()
        dlg = wx.FileDialog(self, message="Save file as", 
                            wildcard=self.__getwildcard(),
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            with open(path, 'w') as f:
                json.dump(values, f, indent=2)
            self.log.WriteText(f"Inputs are saved as {path}")
        dlg.Destroy()

    def OnLoad(self):
        print('Load EKMC inputs ...')
        dlg = wx.FileDialog(self, message="Choose a file",
                            wildcard=self.__getwildcard(),
                            style=wx.FD_OPEN | wx.FD_PREVIEW |
                            wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.log.WriteText(f"Loading")
            path = dlg.GetPath()
            with open(path, 'r') as f:
                values = json.load(f)
            if isinstance(values.get('EKMC'), dict) and values['EKMC'].get('EKMC'):
                self.set_values(values['EKMC'])
            else:
                self.set_values(values)
            self.log.WriteText(f"Inputs are loaded from {path}")
        dlg.Destroy()                    
        pass
    
    def OnInnerSizeChanged(self):
        w,h = self.Box.GetMinSize()
        self.SetVirtualSize((w,h))
        self.Layout()
    
    def OnRunEKMC(self, event=None):
        sj_start = time.time()
        # self.__save()
        # TEST ing, 测试写入EKMC-INPUT
        # print(self.values)
        try:
            with open(self.ekmcPane.iniFilePath, "r") as f:
                with open('data/EKMC-INPUT/ini.xyz', 'w') as kmc_ini:
                    kmc_ini.write(f.read())
            self.__save()
            self.particle = None
        except FileNotFoundError:
            wx.Bell()
            self.log.WriteText("EKMC Error: failed when loading initial strucutre file")
            return
        self.log.WriteText("EKMC Job Initiating...")
        if writeEkmcInp(self.values):
            self.log.WriteText("EKMC Job Started...")
            pwd0 = os.getcwd()
            os.chdir(os.path.join(pwd0, 'data'))
            out = subprocess.Popen("EKMC-main.exe", shell=True, stdout=subprocess.PIPE)
            stdout, stderr = out.communicate()
            if not stderr:
                self.log.Write(stdout)
                sj_elapsed = round(time.time() - sj_start, 4)
                self.log.WriteText('EKMC Job Completed. Total Cost About: ' + str(sj_elapsed) + ' Seconds')
                self.topWin.VisualPanel.ChangeSelection(0)
                try:
                    final_stru_coors = self.topWin.pltPanle.post_ekmc()
                except:
                    self.log.WriteText('EKMC postprocessing failed')
                    os.chdir(pwd0)
                    return
                # TODO - 读取rec_site_spc.xyz并可视化
                new_NP = NanoParticle(final_stru_coors['ele'], 
                                      final_stru_coors[['x', 'y', 'z']], 
                                      covTypes=final_stru_coors[['cov']])
                new_NP.addColorGCN(final_stru_coors[['gcn']])
                new_NP.addColorCN(final_stru_coors[['cn']])
                self.topWin.glPanel.DrawEKMC(new_NP)
            else:
                self.log.WriteText('EKMC Failed: Error when running.')
            os.chdir(pwd0)
        else:
            self.log.WriteText("EKMC Failed: Error when loading inputs")
        
    def PostEKMC(self):
        pass


class EkmcPanel(wx.Panel):
    def __init__(self, parent : InputPanelEKMC):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.log = parent.log
        self.digitValidator = parent.digitValidator
        self.posDigitValidator = parent.posDigitValidator

        self.iniFilePath = ""
        self._bulk_updating = False
        self._reactants_dirty = False

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

        self.win = self # pass
        self.Box = wx.BoxSizer(wx.VERTICAL)
        self.win.SetSizer(self.Box)
        
        nSpe = 1
        self.__initUI()
        self.__initSpecies()
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
        boxh1.Add(wx.StaticText(self.win, label='Read from file'), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        self.fileBtn = wx.Button(self.win, -1, "Select")
        self.fileBtn.Bind(wx.EVT_BUTTON, self.__fileSelect)
        boxh1.Add(self.fileBtn, 0, wx.ALIGN_CENTER|wx.ALL, 8)

        # new - boxsizes
        boxh2 = wx.BoxSizer(wx.HORIZONTAL)
        self.Box.Add(boxh2, 0, wx.EXPAND|wx.ALL)
        boxh2.AddSpacer(self.padding)
        boxh2.Add(wx.StaticText(self.win, label='Simulation box size (\u00C5):'), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        for dim in ['x', 'y', 'z']:
            boxh2.Add(wx.StaticText(self.win, label=dim), 0, wx.ALIGN_CENTER|wx.ALL, 5)
            wgt = wx.TextCtrl(self.win, -1, size=(60, -1), style=wx.TE_CENTRE)
            wgt.SetValidator(self.posDigitValidator)
            boxh2.Add(wgt, 0, wx.EXPAND|wx.ALL, 8)
            self.entries['dim_' + dim] = wgt

        boxh3 = wx.BoxSizer(wx.HORIZONTAL)
        self.Box.Add(boxh3, 0, wx.EXPAND|wx.ALL)
        boxh3.AddSpacer(self.padding)
        boxh3.Add(wx.StaticText(self.win, label='Total steps'), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        wgt = wx.TextCtrl(self.win, -1, size=(120, -1), style=wx.TE_CENTRE)
        wgt.SetValidator(self.posDigitValidator)
        boxh3.Add(wgt, 0, wx.EXPAND|wx.ALL, 8)
        self.entries['nLoop'] = wgt
        # boxh3.AddSpacer(8)
        boxh3.Add(wx.StaticText(self.win, label='Record interval'), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        wgt = wx.TextCtrl(self.win, -1, size=(120, -1), style=wx.TE_CENTRE)
        wgt.SetValidator(self.posDigitValidator)
        boxh3.Add(wgt, 0, wx.EXPAND|wx.ALL, 8)
        self.entries['record_int'] = wgt

        # new - parameters for atom migrations
        ajBox = wx.StaticBox(self.win, -1, 'Atom Migration')
        boxv4 = wx.StaticBoxSizer(ajBox, wx.VERTICAL)
        self.Box.Add(boxv4, 0, wx.EXPAND|wx.ALL)

        boxv4_h1 = wx.BoxSizer(wx.HORIZONTAL)
        boxv4.Add(boxv4_h1, 0, wx.EXPAND|wx.ALL)
        boxv4_h1.AddSpacer(self.padding)
        boxv4_h1.Add(wx.StaticText(self.win, label='Bond energy (eV):     ε_M ='), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        wgt = wx.TextCtrl(self.win, -1, size=(60, -1), style=wx.TE_CENTRE)
        wgt.SetValidator(self.digitValidator)
        # 创建垂直sizer包裹TextCtrl，以实现垂直8像素，水平1像素的边框
        v_sizer_text = wx.BoxSizer(wx.VERTICAL)
        v_sizer_text.Add(wgt, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 8)  # 垂直边距
        boxv4_h1.Add(v_sizer_text, 0, wx.EXPAND|wx.ALL, 1)
        self.entries['E_bond'] = wgt

        boxv4_h2 = wx.BoxSizer(wx.HORIZONTAL)
        boxv4.Add(boxv4_h2, 0, wx.EXPAND|wx.ALL)
        boxv4_h2.AddSpacer(self.padding)
        boxv4_h2.Add(wx.StaticText(self.win, label='Cohesive energy (eV):   U ='), 0, wx.ALIGN_CENTER|wx.ALL, 8)
        # U0
        wgt = wx.TextCtrl(self.win, -1, size=(60, -1), style=wx.TE_CENTRE)
        wgt.SetValidator(self.digitValidator)
        # 创建垂直sizer包裹TextCtrl，以实现垂直8像素，水平1像素的边框
        v_sizer_text = wx.BoxSizer(wx.VERTICAL)
        v_sizer_text.Add(wgt, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 8)  # 垂直边距
        boxv4_h2.Add(v_sizer_text, 0, wx.EXPAND|wx.ALL, 1)
        self.entries['Ecoh_U0'] = wgt

        boxv4_h2.Add(wx.StaticText(self.win, label='*('), 0, wx.ALIGN_CENTER|wx.ALL, 1)
        # A1
        wgt = wx.TextCtrl(self.win, -1, size=(60, -1), style=wx.TE_CENTRE)
        wgt.SetValidator(self.digitValidator)
        v_sizer_text = wx.BoxSizer(wx.VERTICAL)
        v_sizer_text.Add(wgt, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 8)  # 垂直边距
        boxv4_h2.Add(v_sizer_text, 0, wx.EXPAND|wx.ALL, 1)
        self.entries['Ecoh_A1'] = wgt

        boxv4_h2.Add(wx.StaticText(self.win, label='*exp(-GCN/'), 0, wx.ALIGN_CENTER|wx.ALL, 1)
        # t1
        wgt = wx.TextCtrl(self.win, -1, size=(60, -1), style=wx.TE_CENTRE)
        wgt.SetValidator(self.digitValidator)
        v_sizer_text = wx.BoxSizer(wx.VERTICAL)
        v_sizer_text.Add(wgt, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 8)  # 垂直边距
        boxv4_h2.Add(v_sizer_text, 0, wx.EXPAND|wx.ALL, 1)
        self.entries['Ecoh_t1'] = wgt

        boxv4_h2.Add(wx.StaticText(self.win, label=') + '), 0, wx.ALIGN_CENTER|wx.ALL, 1)
        # A2
        wgt = wx.TextCtrl(self.win, -1, size=(60, -1), style=wx.TE_CENTRE)
        wgt.SetValidator(self.digitValidator)
        v_sizer_text = wx.BoxSizer(wx.VERTICAL)
        v_sizer_text.Add(wgt, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 8)  # 垂直边距
        boxv4_h2.Add(v_sizer_text, 0, wx.EXPAND|wx.ALL, 1)
        self.entries['Ecoh_A2'] = wgt

        boxv4_h2.Add(wx.StaticText(self.win, label='*exp(-GCN/'), 0, wx.ALIGN_CENTER|wx.ALL, 1)
        # t2
        wgt = wx.TextCtrl(self.win, -1, size=(60, -1), style=wx.TE_CENTRE)
        wgt.SetValidator(self.digitValidator)
        v_sizer_text = wx.BoxSizer(wx.VERTICAL)
        v_sizer_text.Add(wgt, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 8)  # 垂直边距
        boxv4_h2.Add(v_sizer_text, 0, wx.EXPAND|wx.ALL, 1)
        self.entries['Ecoh_t2'] = wgt

        boxv4_h2.Add(wx.StaticText(self.win, label=') + 1)'), 0, wx.ALIGN_CENTER|wx.ALL, 1)

    def __initSpecies(self):
        speBox = wx.StaticBox(self.win, -1, '')
        speSizer = wx.StaticBoxSizer(speBox, wx.VERTICAL)
        self.Box.Add(speSizer, 0, wx.EXPAND|wx.ALL)

        self.spePane = SpeciePane(self, self.win, SpecieRowEKMC)
        speSizer.Add(self.spePane)

    def __initEvents(self):
        evtBox = wx.StaticBox(self.win, -1, '')
        evtSizer = wx.StaticBoxSizer(evtBox, wx.VERTICAL)
        self.Box.Add(evtSizer, 0, wx.EXPAND|wx.ALL)

        self.evtPane = EventPaneEKMC(self, self.win)
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

    def __beginBulkUpdate(self):
        self._bulk_updating = True
        self._reactants_dirty = False
        for win in (self.parent, self.win, self.spePane, self.evtPane):
            try:
                win.Freeze()
            except Exception:
                pass

    def __markReactantsDirty(self):
        if self._bulk_updating:
            self._reactants_dirty = True
            return True
        return False

    def __refreshEventReactants(self):
        for evtRow in np.append(self.evtPane.mobRows, self.evtPane.fixRows):
            evtRow.updateReactants()

    def __endBulkUpdate(self):
        try:
            if self._reactants_dirty:
                self.__refreshEventReactants()
        finally:
            self._reactants_dirty = False
            for win in (self.evtPane, self.spePane, self.win, self.parent):
                try:
                    win.Thaw()
                except Exception:
                    pass
            self._bulk_updating = False
            self.parent.OnInnerSizeChanged()

    def __fileSelect(self, event):
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultFile=self.iniFilePath,
            wildcard=("xyz files (*.xyz)|*.xyz|"
                        "All files (*.*)|*.*"),
            style=wx.FD_OPEN | wx.FD_PREVIEW |
                    wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.log.WriteText(f"xyz File selected")
            self.iniFilePath = dlg.GetPath()
            self.log.WriteText(f"xyz File selected :{self.iniFilePath}")


    def updateIdMap_twosite(self, id, name):
        try:
            self.id2reactantMap[id] = f"{name}@i*"
            self.id2reactantMap[-id] = f"{name}@j*"
            if self.__markReactantsDirty():
                return
            self.__refreshEventReactants()
        except bidict.ValueDuplicationError:
            self.log.WriteText("Please ensure the unique of name")
        # print(self.id2reactantMap)

    def updateIdMap(self, id, name):
        if type(id) == int:
            name = name + "*"
        try:
            self.id2reactantMap[id] = name
            if self.__markReactantsDirty():
                return
            self.__refreshEventReactants()
        except bidict.ValueDuplicationError:
            self.log.WriteText("Please ensure the unique of name")
        # print(self.id2reactantMap)
    
    def popIdMap_twosite(self, id):
        self.id2reactantMap.pop(id)
        self.id2reactantMap.pop(-id)
        if self.__markReactantsDirty():
            return
        self.__refreshEventReactants()

    def popIdMap(self, id):
        self.id2reactantMap.pop(id)
        if self.__markReactantsDirty():
            return
        self.__refreshEventReactants()
        # print(self.id2reactantMap)

    def OnSave(self):
        self.values = {}
        for key, widget in self.entries.items():
            self.values[key] = widget.GetValue()
        self.values['iniFilePath'] = self.iniFilePath
        self.values['nspecies'] = self.nspecies
        self.values['nevents'] = self.nevents
        self.values['nevents_mob'] = self.evtPane.getNmobE()
        for i, spe in enumerate(self.species):
            self.values[f"s{i+1}"] = json.dumps(spe, cls=Specie.Encoder)
        # initiate num_gen/consum and event_gen/consum of products
        for pro in self.products:
            pro.reset()
        self.events = self.evtPane.OnSave()
        for i, evt in enumerate(self.events):
            self.values[f"e{i+1}"] = json.dumps(evt, cls=Event.Encoder)
        li = self.liWin.getValues()
        if li != None:
            self.values["li"] = self.liWin.getValues()
        else:
            self.log.WriteText("Error when save li in kmc module, please check")
        return self.values

    def OnLoad(self, values : dict):
        self.__beginBulkUpdate()
        try:
            self.values = values
            self.iniFilePath = self.values.get('iniFilePath', self.iniFilePath)
            for key, widget in self.entries.items():
                widget.SetValue(self.values.get(key, ''))
            if self.values.get('nspecies'):
                self.spePane.setSpes(nSpe=self.values['nspecies'])
            # if self.values.get('nproducts'):
            #     self.proPane.setPros(nPro=self.values['nproducts'])
            if self.values.get('nevents'):
                nEvt = self.values['nevents']
                nMob = self.values.get('nevents_mob', nEvt)
                self.evtPane.setEvts(nEvt, nMob)
            if self.values.get('li'):
                self.liWin.setValues(self.values['li'])
        finally:
            self.__endBulkUpdate()


# 与SepcieRow的区别，默认is_twosite是false，不可以改
class EventPaneEKMC(wx.Panel):
    def __init__(self, master : EkmcPanel, parent):
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

        self.mainBox.Add(box)

    def __addEvt(self, box, newEvt=None):
        self.master.nevents += 1
        if not newEvt:
            newEvt = Event()
        newRow = EventRowEKMC(self, newEvt)
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
        if not getattr(self.master, '_bulk_updating', False):
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
                        newRow = self.addFixEvt(newEvt, False)
                        self.master.spePane.rows[newEvt.toggle_spe - 1].bindEvt(newEvt, newRow)
                else:
                    self.mobRows[n].setEvt(newEvt)
                    n += 1
                    if n > self._nMobEvnets:
                        self.log.WriteText("Warning: error happens when loading events, please check the 'toggled' value of events")
        self.evtLabel.SetLabel(f"{self.master.nevents}")
        if not getattr(self.master, '_bulk_updating', False):
            self.master.parent.OnInnerSizeChanged()

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


class EventRowEKMC(wx.Panel):
    def __init__(self, parent : EventPaneEKMC, evt : Event):
        wx.Panel.__init__(self, parent)
        self.master = parent.master
        self.padding = parent.padding
        self.width = parent.width
        self.event = evt
        self.digitValidator = parent.master.digitValidator
        self.posDigitValidator = parent.master.posDigitValidator

        self._destroyed = False
        self._types = ["Adsorption", "Desorption", 
                       "Diffusion"]
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

    def __OnType(self, event):
        obj = event.GetEventObject()
        name = obj.Name
        value = obj.GetValue()
        self.onTextChange(event, self.event, name, value)
        self.BEPrBtn.Enable(value=="Adsorption")

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
            self.subEntries["E_ads_para"][1].Enable(obj.GetValue())

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
            elif key == "BEP_para":
                wgt[0].SetValue(f"{value[0]}")
                wgt[1].SetValue(f"{value[1]}")
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


class SpecieRowEKMC(wx.Panel):
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
        siteWin = self.__CreateSitePopWin()
        siteBtn.Bind(wx.EVT_BUTTON, lambda event: self.__onShowPopup(event, siteWin))
        self._btnDict["is_twosite"] = siteBtn
        # new
        siteOnOff.Disable(True)
        

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
        diffWin = self.__CreateDiffPopWin()
        diffBtn.Bind(wx.EVT_BUTTON, lambda event: self.__onShowPopup(event, diffWin))
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
    
    def __CreateSitePopWin(self):
        popWin = wx.PopupTransientWindow(
            self, flags=wx.SIMPLE_BORDER|wx.PU_CONTAINS_CONTROLS)
        popWin.SetBackgroundColour(POP_BG_COLOR)
        popWin.SetFont(GET_FONT())
        
        popBox = wx.BoxSizer(wx.VERTICAL)
        popWin.SetSizer(popBox)

        popBox.Add(wx.StaticText(popWin, -1, "E_ads = k₁GCNᵢ (+ k₂GCNⱼ) + b"),
                   0, wx.ALIGN_CENTER|wx.ALL, 6)
        tip = wx.StaticText(popWin, -1, "k₂ is needed for two-site species")
        tip.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT,
                            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,
                            False, 'Calibri'))
        tip.SetForegroundColour("grey")
        popBox.Add(tip, 0, wx.ALIGN_CENTER|wx.ALL, 6)

        etyBox1 = wx.BoxSizer(wx.HORIZONTAL)
        etyBox2 = wx.BoxSizer(wx.HORIZONTAL)
        etyBox3 = wx.BoxSizer(wx.HORIZONTAL)
        BEPk1Ety = wx.TextCtrl(popWin, -1, size=(100, -1), style=wx.TE_CENTER, name="E_ads0")
        BEPk2Ety = wx.TextCtrl(popWin, -1, size=(100, -1), style=wx.TE_CENTER, name="E_ads1")
        BEPbEty = wx.TextCtrl(popWin, -1, size=(100, -1), style=wx.TE_CENTER, name="E_ads2")
        BEPk1Ety.Bind(wx.EVT_TEXT, lambda event: self.onTextChange(event, self.sepcie, 'E_ads0'))
        BEPk2Ety.Bind(wx.EVT_TEXT, lambda event: self.onTextChange(event, self.sepcie, 'E_ads1'))
        BEPbEty.Bind(wx.EVT_TEXT, lambda event: self.onTextChange(event, self.sepcie, 'E_ads2'))
        self.subEntries["E_ads_para"] = [BEPk1Ety, BEPk2Ety, BEPbEty]
        etyBox1.Add(wx.StaticText(popWin, -1, "k₁"), 0, wx.ALIGN_CENTER|wx.ALL, 5)
        etyBox1.Add(BEPk1Ety, 0, wx.ALIGN_CENTER|wx.ALL, 3)
        etyBox2.Add(wx.StaticText(popWin, -1, "k₂"), 0, wx.ALIGN_CENTER|wx.ALL, 5)
        etyBox2.Add(BEPk2Ety, 0, wx.ALIGN_CENTER|wx.ALL, 3)
        etyBox3.Add(wx.StaticText(popWin, -1, "b"), 0, wx.ALIGN_CENTER|wx.ALL, 5)
        etyBox3.Add(BEPbEty, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        popBox.Add(etyBox1, 0, wx.ALIGN_CENTER|wx.ALL, 3)
        popBox.Add(etyBox2, 0, wx.ALIGN_CENTER|wx.ALL, 3)
        popBox.Add(etyBox3, 0, wx.ALIGN_CENTER|wx.ALL, 3)

        popBox.Fit(popWin)
        popWin.Layout()

        return popWin

    def __CreateDiffPopWin(self):
        popWin = wx.PopupTransientWindow(
            self, flags=wx.SIMPLE_BORDER|wx.PU_CONTAINS_CONTROLS)
        popWin.SetBackgroundColour(POP_BG_COLOR)
        popWin.SetFont(GET_FONT())
        
        popBox = wx.BoxSizer(wx.HORIZONTAL)
        popWin.SetSizer(popBox)

        EaDiffEty = wx.TextCtrl(popWin, -1, size=(100, -1), style=wx.TE_CENTER, name="Ea_diff")
        EaDiffEty.Bind(wx.EVT_TEXT, lambda event: self.onTextChange(event, self.sepcie, 'Ea_diff'))
        self.subEntries["Ea_diff"] = EaDiffEty
        
        popBox.Add(wx.StaticText(popWin, -1, "Diffusion energy Barriar (eV)"),
                   0, wx.ALIGN_CENTER|wx.ALL, 6)
        popBox.Add(EaDiffEty, 0, wx.ALIGN_CENTER|wx.ALL, 6)

        popBox.Fit(popWin)
        popWin.Layout()
        
        return popWin

    def __SwOnOff(self, event):
        obj = event.GetEventObject()
        name = obj.Name
        self.onTextChange(event, self.sepcie, name)
        if (name == "is_twosite"):
            self.__DisableEvtOnoff(obj.GetValue())
            self.subEntries["E_ads_para"][1].Enable(obj.GetValue())
            if obj.GetValue():
                self.master.updateIdMap_twosite(self.id, self.sepcie.getName())
            else:
                if self.master.id2reactantMap.get(-self.id):
                    self.master.id2reactantMap.pop(-self.id)
                self.master.updateIdMap(self.id, self.sepcie.getName()) ## idMap
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
        self._btnDict["flag_ads"].Enable(not spe.is_twosite and (spe.flag_ads or spe.flag_des))

        self.subEntries["flag_diff"].SetValue(spe.flag_diff)
        self._btnDict["flag_diff"].Enable(spe.flag_diff)

        self.subEntries["is_twosite"].SetValue(spe.is_twosite)
        self.subEntries["Ea_diff"].SetValue(f"{spe.Ea_diff}")

        for i in range(3):
            self.subEntries["E_ads_para"][i].SetValue(f"{spe.E_ads_para[i]}")

        self.__DisableEvtOnoff(spe.is_twosite)
        
        self.adsDesWin.setValues(spe.getAdsDesAttr())

    def __DisableEvtOnoff(self, flag : bool):
        self.subEntries["E_ads_para"][1].Enable(flag)
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
                    self._rowDict[key] = None
            else:
                onoff.Enable()
        if flag and not getattr(self.master, '_bulk_updating', False):
            self.master.parent.OnInnerSizeChanged()

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
        for name, row in self._rowDict.items():
            if row:
                self.master.evtPane.delFixEvt(row, True)
                self._rowDict[name] = None
        self.Destroy()


if __name__ == '__main__':
    class MyApp(wx.App):
        """
        TextCtrlWithImage Application.
        """
        def OnInit(self):
            """
            Create the TextCtrlWithImage application.
            """
            
            frame = wx.Frame(None, title="EKMC-test", size=(800, 600))
            frame.SetBackgroundColour(BG_COLOR)
            panel = InputPanelEKMC(frame, None)
            frame.Show(True)
            
            return True
        
    app = MyApp(redirect=False)
    app.MainLoop()
