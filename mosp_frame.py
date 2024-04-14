# -*- coding: utf-8 -*-
"""
@author: yinglei
"""

import ttkbootstrap as ttk
import tkinter as tk
import win32api
import os
import sys
import json
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showinfo


def handlerAdaptor(fun, **kwds):
    # Adaptors for event handlers
    return lambda event: fun(event, **kwds)


class FacesFrame(tk.Frame):
    def __init__(self,
                 parent,
                 header,
                 items,
                 initial_num=3,
                 scrollframe=None,
                 scrollcanvas=None):
        tk.Frame.__init__(self, parent)
        self.num_faces = 0
        self.items = items
        self.height = win32api.GetSystemMetrics(1)
        self.width = win32api.GetSystemMetrics(0)
        self.mainframe = scrollframe
        self.canvas = scrollcanvas

        self.textboxes = []
        self.parententries = []  # entries that where direct to new subwindow
        self.entries = [] # list of dicts
        self.values = {}
        self.values['num_faces'] = self.num_faces

        # create label to display number of faces
        self.num_label = tk.Label(self, text="Number of faces: " + str(self.num_faces))
        self.num_label.grid(row=0, column=0)

        # create button to add new face
        self.add_button = ttk.Button(self,
                                     text="Add",
                                     bootstyle=(ttk.DARK, ttk.OUTLINE),
                                     width=7,
                                     command=self.__add_face)
        self.add_button.grid(row=0, column=1, padx=5, pady=5)

        # create button to remove last face
        self.remove_button = ttk.Button(self,
                                        text="Remove",
                                        bootstyle=(ttk.DARK, ttk.OUTLINE),
                                        width=7,
                                        command=self.__remove_face)
        self.remove_button.grid(row=0, column=2, padx=5, pady=5)

        # create header
        for i, t in enumerate(header):
            tk.Label(self, text=t)\
                .grid(row=1, column=i, padx=5, pady=5, sticky=tk.W+tk.E)

        # create initial textbox
        self.set_num_faces(initial_num)

    @staticmethod
    def __unset(var):
        var.set("unset")

    @staticmethod
    def __set(var):
        var.set("set")

    def __update_scroll_region(self):
        if self.mainframe and self.canvas:
            self.mainframe.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def __add_face(self):
        # increment number of faces and update label
        self.num_faces += 1
        self.num_label.config(text="Number of faces: " + str(self.num_faces))
        # create new textbox and add it to list
        new_textbox = []
        new_entry = {}
        new_parententry = {}
        for j, item in enumerate(self.items):
            var = tk.StringVar()
            widget = ttk.Entry(self, textvariable=var, width=16, justify="center")
            new_textbox.append(widget)
            widget.grid(row=self.num_faces + 1, column=j, padx=5, pady=5)
            i = self.num_faces - 1
            if item == "E_ads" or item == "S_ads":
                self.__unset(var)
                new_parententry[f'{i}_{item}'] = (var, widget)
                widget.config(state="readonly")
                widget.bind(
                    "<Button-1>",
                    handlerAdaptor(self.__show_ads_window, ID=i, p_name=f'{i}_{item}'))
            elif item == "w":
                self.__unset(var)
                new_parententry[f'{i}_{item}'] = (var, widget)
                widget.config(state="readonly")
                widget.bind(
                    "<Button-1>",
                    handlerAdaptor(self.__show_w_window, ID=i, p_name=f'{i}_{item}'))
            else:
                new_entry[f'{self.num_faces-1}_{item}'] = (var, widget)
        self.textboxes.append(new_textbox)
        self.entries.append(new_entry)
        self.parententries.append(new_parententry)
        self.values[self.num_faces - 1] = {}
        self.values['num_faces'] = self.num_faces
        self.__update_scroll_region()

    def __remove_face(self):
        if self.num_faces > 1:
            # decrement number of textboxes and update label
            self.num_faces -= 1
            self.num_label.config(text=f"Number of faces: {self.num_faces}")
            # remove last textbox from grid and list
            for textbox in self.textboxes[-1]:
                textbox.destroy()
            del self.textboxes[-1]
            del self.entries[-1]
            del self.parententries[-1]
            self.values.pop(self.num_faces)
            self.values['num_faces'] = self.num_faces
            self.__update_scroll_region()

    def __show_ads_window(self, event, ID, p_name):
        # ID is the id of faces
        # p_name is the name of this window and the prefix of subentries-name
        ads_window = tk.Toplevel(self)
        ads_window.title("Adsorption")
        ads_window.geometry('280x250+{}+{}'.format(int(self.width * 0.4),
                                                   int(self.height * 0.4)))

        # create subentires and record (var, entry)
        sub_items = ["Gas1", "Gas2", "Gas3"]
        for i, item in enumerate(sub_items):
            ttk.Label(ads_window, text=item)\
                .grid(row=i, column=0, padx=5, pady=5)
            var = tk.StringVar()
            newEntry = ttk.Entry(ads_window, textvariable=var, width=12)
            newEntry.focus()
            name = f'{p_name}_{item}'
            self.entries[ID][name] = (var, newEntry)
            newEntry.grid(row=i, column=1, padx=5, pady=5)
            # check if values have been set
            if self.values[ID].get(name, 0):
                var.set(self.values[ID][name])
                self.__set(self.parententries[ID][p_name][0])

        # create Save button
        save_button = ttk.Button(
            ads_window,
            text="Save",
            bootstyle=(ttk.DARK, ttk.OUTLINE),
            command=lambda:
            [self.save_subentry(ID, p_name, sub_items),
             ads_window.destroy()])
        save_button.grid(row=i + 1, column=1, padx=5, pady=5, sticky=tk.E)

        return ads_window

    def __show_w_window(self, event, ID, p_name):
        # ID is the id of faces
        # name is the name of this window and the p_name of subentries
        w_window = tk.Toplevel(self)
        w_window.title("Adsorption")
        w_window.geometry('280x350+{}+{}'.format(int(self.width * 0.4),
                                                 int(self.height * 0.3)))

        sub_items = [
            "Gas1-Gas1", "Gas1-Gas2", "Gas1-Gas3", "Gas2-Gas2", "Gas2-Gas3", "Gas3-Gas3"
        ]
        for i, item in enumerate(sub_items):
            ttk.Label(w_window, text=item).grid(row=i, column=0, padx=5, pady=5)
            var = tk.StringVar()
            newEntry = ttk.Entry(w_window, textvariable=var, width=12)
            newEntry.focus()
            name = f'{p_name}_{item}'
            self.entries[ID][name] = (var, newEntry)
            newEntry.grid(row=i, column=1, padx=5, pady=5)
            # check
            if self.values[ID].get(name, 0):
                var.set(self.values[ID][name])
                self.__set(self.parententries[ID][p_name][0])

        # create Save button
        save_button = ttk.Button(
            w_window,
            text="Save",
            bootstyle=(ttk.DARK, ttk.OUTLINE),
            command=lambda:
            [self.save_subentry(ID, p_name, sub_items),
             w_window.destroy()])
        save_button.grid(row=i + 1, column=1, padx=5, pady=5, sticky=tk.E)

        return w_window

    def set_num_faces(self, n):
        while (self.num_faces != n):
            if (self.num_faces < n):
                self.__add_face()
            else:
                self.__remove_face()

    def save_subentry(self, ID, p_name, items):
        # get the values of all subentries
        # change the display of parent entry if values are set
        Parent_e = self.parententries[ID][p_name]
        for item in items:
            name = f'{p_name}_{item}'
            (var, _) = self.entries[ID][name]
            value = var.get()
            self.values[ID][name] = value
            if value:
                self.__set(Parent_e[0])

    def save_frame_entry(self):
        for i, entry in enumerate(self.entries):
            for name, (var, _) in entry.items():
                self.values[i][name] = var.get()
        return self.values

    def read_frame_entry(self, values):
        n = values['num_faces']
        self.set_num_faces(n)
        # reset display of parent entries
        for _, p_dict in enumerate(self.parententries):
            for _, Parent_e in p_dict.items():
                self.__unset(Parent_e[0])
        # reset display of parent entries and check subentries
        for key, value in values.items():
            try:
                self.values[int(key)] = value
                # check to set
                for subkey, subentry in value.items():
                    ID = int(key)
                    p_name, _, _ = subkey.rpartition("_")
                    if subentry and self.parententries[ID].get(p_name, 0):
                        Parent_e = self.parententries[ID][p_name]
                        self.__set(Parent_e[0])
            except ValueError:
                self.values[key] = value
        for i, entry in enumerate(self.entries):
            for name, (var, _) in entry.items():
                try:
                    var.set(self.values[i][name])
                except KeyError:
                    pass
        return self.values


class Specie():
    def __init__(self, name):
        self.name = name
        self.mass = 0.0
        self.PP_ratio = 0.0
        self.S_gas = 0.0
        self.sticking = [1.0, 1.0]
        self.Ea_diff = 0.0
        self.E_ads_para = [0.0, 0.0, 0.0]

        self.is_twosite = False
        self.flag_ads = False
        self.flag_des = False
        self.flag_diff = False


class Product():
    def __init__(self, name):
        self.name = name
        self.num_gen = 0
        self.event_gen = []
        self.num_consum = 0
        self.event_consum = []


class Event():
    def __init__(self, name):
        self.name = name
        self.type = ""
        self.is_twosite = False
        self.cov_before = [0, 0]
        self.cov_after = [0, 0]
        self.BEP_para = [0.0, 0.0]


class KmcFrame(tk.Frame):
    def __init__(self, parent,):
        tk.Frame.__init__(self, parent)
        self.entries = {}
        self.values = {}
        self.center = tk.W + tk.E + tk.S + tk.N
        self.nspecies = 0
        self.nproducts = 0
        self.nevents = 0
        self.species = []
        self.products = []
        self.events = []
        self.react2id_map = {}
        # initial structure set
        f_struct = tk.Frame(self)
        self.__create_f_struct(f_struct)
        f_struct.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        # frame of record
        f_record = tk.Frame(self)
        self.__create_f_record(f_record)
        f_record.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        # frame of species
        f_species = tk.Frame(self)
        self.__create_f_species(f_species)
        f_species.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        # frame of products
        f_products = tk.Frame(self)
        self.__create_f_products(f_products)
        f_products.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        # frame of events
        f_events = tk.Frame(self)
        self.__create_f_events(f_events)
        f_events.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        # frame of lateral interaction
        f_lat = tk.Frame(self)
        self.__create_f_lat(f_lat)
        f_lat.grid(row=5, column=0, padx=5, sticky=tk.W)

    def __create_f_struct(self, frame):
        tk.Label(frame, text="Initial structure: ")\
            .grid(row=0, column=0, sticky=tk.W)
        self.stru_var = tk.IntVar()
        s1 = ttk.Radiobutton(frame, text="MSR Structure", value=0,
                             variable=self.stru_var, bootstyle=(ttk.LIGHT))
        s1.grid(row=0, column=1, padx=5, sticky=tk.W)
        s2 = ttk.Radiobutton(frame, text="Read from file", value=1,
                             command=self.__read_struct_path,
                             variable=self.stru_var, bootstyle=(ttk.LIGHT))
        s2.grid(row=0, column=2, padx=5, sticky=tk.W)

    def __create_f_record(self, frame):
        tk.Label(frame, text="Total steps:")\
            .grid(row=0, column=0, sticky=tk.W)
        var = tk.StringVar()
        widget = ttk.Entry(frame, textvariable=var, width=10, justify="center")
        widget.grid(row=0, column=1, padx=5, sticky=tk.W)
        self.entries["nLoop"] = var, widget
        tk.Label(frame, text="Record interval:")\
            .grid(row=0, column=2, padx=5, sticky=tk.W)
        var = tk.StringVar()
        widget = ttk.Entry(frame, textvariable=var, width=10, justify="center")
        widget.grid(row=0, column=3, padx=5, sticky=tk.W)
        self.entries["record_int"] = var, widget    

    def __create_f_species(self, frame):
        tk.Label(frame, text="Number of adsorbed species:")\
            .grid(row=0, column=0, sticky=tk.W)
        self.label_nspecise = tk.Label(frame, text=self.nspecies)
        self.label_nspecise.grid(row=0, column=1, padx=5, sticky=tk.W)
        button = ttk.Button(frame, text="more..", bootstyle=(ttk.DARK, ttk.OUTLINE),
                            width=6, command=self.__species_subwin)
        button.grid(row=0, column=2, sticky=tk.W)
        
    def __create_f_products(self, frame):
        tk.Label(frame, text="Number of products:")\
            .grid(row=0, column=0, sticky=tk.W)
        self.label_nproducts = tk.Label(frame, text=self.nproducts)
        self.label_nproducts.grid(row=0, column=1, padx=5, sticky=tk.W)
        button = ttk.Button(frame, text="more..", bootstyle=(ttk.DARK, ttk.OUTLINE),
                            width=6, command=self.__prodcut_subwin)
        button.grid(row=0, column=2, sticky=tk.W)

    def __create_f_events(self, frame):
        tk.Label(frame, text="Number of events:")\
            .grid(row=0, column=0, sticky=tk.W)     
        self.label_nevents = tk.Label(frame, text=self.nevents)
        self.label_nevents.grid(row=0, column=1, padx=5, sticky=tk.W)
        button = ttk.Button(frame, text="more..", bootstyle=(ttk.DARK, ttk.OUTLINE),
                            width=6, command=self.__event_subwin)
        button.grid(row=0, column=2, sticky=tk.W)   

    def __create_f_lat(self, frame):
        tk.Label(frame, text="Average lateral interaciont(eV):")\
            .grid(row=0, column=0, pady=5, sticky=tk.W)     

    def __read_struct_path(self):
        self.stru_filename = askopenfilename(title="Select the initial structure file", \
                                             filetypes=(("xyz files", "*.xyz"),))
        if not self.stru_filename:
            self.stru_var.set(0)
            return
        
    def __species_subwin(self):
        subwin = tk.Toplevel(self)
        Specie_win(subwin, self.label_nspecise, self.species)
        
    def __prodcut_subwin(self):
        subwin = tk.Toplevel(self)
        Product_win(subwin, self.label_nproducts, self.products)

    def __event_subwin(self):
        subwin = tk.Toplevel(self)
        self.__update_react_map()
        Event_win(subwin, self.label_nevents, self.events, 
                  self.products, self.react2id_map)

    def __update_react_map(self):
        self.react2id_map = {}
        self.react2id_map["*"] = 0
        for n, spe in enumerate(self.species):
            if spe.is_twosite:
                self.react2id_map[spe.name+"@i*"] = n + 1
                self.react2id_map[spe.name+"@j*"] = -1 * (n+1)
            else:
                self.react2id_map[spe.name+"*"] = n + 1
        for n, p in enumerate(self.products):
            self.react2id_map[p.name] = 'p' + str(n + 1)

    def ini_specie(self, n, spe_list, Sgas_list, pp_list):
        self.label_nspecise.config(text = self.nspecies)
        self.nspecies = n
        self.species = []
        for n, name in enumerate(spe_list):
            newSpe = Specie(name)
            newSpe.flag_ads = True
            newSpe.flag_des = True
            newSpe.S_gas = Sgas_list[n]
            newSpe.PP_ratio = pp_list[n]
            self.species.append(newSpe)

    def get_entries(self):
        for name, (var, _) in self.entries.items():
            self.values[name] = var.get()
        self.values["nspecies"] = len(self.species)
        self.values["nproducts"] = len(self.products)
        self.values["nevents"] = len(self.events)
        print(self.values)
        for spe in self.species:
            print(spe.__dict__)
        return self.values

    def save_entery(self):
        self.get_entries()
        # save the data in a user-defined file
        filename = asksaveasfilename(defaultextension='.txt', initialfile='kmc')
        if not filename:
            return
        with open(filename, 'w') as f:
            json.dump(self.values, f, indent=2)
        # save initial structure if user selects a *.xyz file
        if self.stru_var.get():
            with open(self.stru_filename, "r") as f:
                with open('ini.xyz', 'w') as kmc_ini:
                    kmc_ini.write(f.read())
        showinfo("Save", "Inputs have been saved")

    def read_entries(self):
        filename = askopenfilename()
        if not filename:
            return
        with open(filename, "r") as f:
            values = json.load(f)
        frame_values = {}
        for key, value in values.items():
            if self.entries.get(key):
                self.values[key] = value
                (var, _) = self.entries[key]
                var.set(value)
            else:
                frame_values[key] = value


class Scrollable_win:
    def __init__(self, window):
        self.window = window
        self.height = win32api.GetSystemMetrics(1)
        self.width = win32api.GetSystemMetrics(0)
        self.canvas = tk.Canvas(self.window)
        self.mainframe = tk.Frame(self.canvas)
        self.mainframe.pack(expand=1, fill="both")
        # Set rollabel region
        self.canvas.create_window(0, 0, anchor=tk.NW, window=self.mainframe)
        self.mainframe.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        # Create Scrollbars and relate them to Canvas
        self.hscrollbar = ttk.Scrollbar(self.window, orient=tk.HORIZONTAL, 
                                        command=self.canvas.xview)
        self.vscrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL,
                                        command=self.canvas.yview)
        # bind wheel to vscrollbar if focus
        self.mainframe.bind('<Enter>', self._bound_to_mousewheel)
        self.mainframe.bind('<Leave>', self._unbound_to_mousewheel)
        self.canvas.configure(xscrollcommand=self.hscrollbar.set,
                              yscrollcommand=self.vscrollbar.set)
        # Set location of canvas and scrollbars
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.hscrollbar.place(relx=0, rely=1.0, relwidth=1.0, anchor=tk.SW)
        self.vscrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor=tk.NE)

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def update_scroll_region(self):
        self.mainframe.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))


class Specie_win(Scrollable_win):
    def __init__(self, window, label, species):
        super(Specie_win, self).__init__(window)
        self.window.title("Species")
        self.window.geometry('{}x{}+55+55'.format(int(self.width * 0.85), 
                                                  int(self.height * 0.8)))
        self.frame = tk.Frame(self.mainframe)
        self.frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5)
        self.species = species
        self.nspecies = len(species)
        self.label = label
        self.entries = [] # list of dicts
        self.row_frames = []
        self.rows = []
        for n, specie in enumerate(self.species):
            self.__add_row(n, specie)
        add_button = ttk.Button(self.mainframe, text="Add", 
                                bootstyle=(ttk.DARK, ttk.OUTLINE), 
                                width=7, command=self.__add)
        add_button.grid(row=1, column=0, padx=5, pady=5)
        del_button = ttk.Button(self.mainframe, text="Delete", 
                                bootstyle=(ttk.DARK, ttk.OUTLINE), 
                                width=7, command=self.__delete)
        del_button.grid(row=1, column=1, padx=5, pady=5)
        save_button = ttk.Button(self.mainframe, text="Save", 
                                bootstyle=(ttk.DARK, ttk.OUTLINE), 
                                width=7, command=self.__save)
        save_button.grid(row=1, column=2, padx=5, pady=5)
        # print(self.entries)

    def __add(self):
        newSpe = Specie("")
        self.species.append(newSpe)
        self.nspecies += 1
        self.__add_row(self.nspecies, newSpe)

    def __add_row(self, n, specie):
        row_frame = tk.Frame(self.frame)
        row_frame.grid(row=n, column=0)
        row = Specie_row(row_frame, specie)
        self.row_frames.append(row_frame)
        self.rows.append(row)
        self.entries.append(row.spe_entries)
        # update rollabel region
        super().update_scroll_region()        

    def __delete(self):
        if self.nspecies > 1:
            del self.rows[-1]
            self.row_frames[-1].destroy()
            del self.row_frames[-1]
            del self.species[-1]
            self.nspecies -= 1
            # update rollabel region
            super().update_scroll_region()        

    def __save(self):
        for n, spe in enumerate(self.species):
            spe_entries = self.entries[n]
            spe.name = spe_entries["name"][0].get()
            spe.mass = spe_entries["mass"][0].get()
            spe.PP_ratio = spe_entries["PP_ratio"][0].get()
            spe.S_gas = spe_entries["S_gas"][0].get()
            spe.sticking = [spe_entries["S0_f"][0].get(), 
                            spe_entries["S0_ce"][0].get()]
            spe.Ea_diff = spe_entries["Ea_diff"][0].get()
            spe.E_ads_para = [spe_entries["Sgcn_ki"][0].get(),
                              spe_entries["Sgcn_kj"][0].get(),
                              spe_entries["Sgcn_b"][0].get()]

            spe.flag_ads = spe_entries["flag_ads"][0].get()
            spe.flag_des = spe_entries["flag_des"][0].get()
            spe.flag_diff = spe_entries["flag_diff"][0].get()
            spe.is_twosite = spe_entries["is_twosite"][0].get()
            # print(spe.__dict__)
            # print(spe_entries.keys())
        self.label.config(text = self.nspecies)
        self.window.destroy()


class Specie_row(tk.Frame):
    def __init__(self, master, specie):
        super().__init__(master)
        self.spe_entries = {}

        name_var = tk.StringVar()
        name_var.set(specie.name)
        name_entry = ttk.Entry(master, textvariable=name_var, width=8, justify="center")
        name_entry.grid(row=0, column=0, padx=5, pady=5)
        self.spe_entries["name"] = (name_var, name_entry)

        # Ads/Des
        f_ads_des = tk.LabelFrame(master, bd=1)
        f_ads_des.grid(row=0, column=1, pady=5)
        sf_check_ads_des = ttk.Frame(f_ads_des)
        sf_entry_ads_des = ttk.Frame(f_ads_des)
        sf_entry_ads_des_2 = ttk.Frame(f_ads_des)
        sf_check_ads_des.grid(row=0, column=0, pady = 5)
        sf_entry_ads_des.grid(row=1, column=0, pady = 5)
        sf_entry_ads_des_2.grid(row=2, column=0, pady = 5)
        ads_var = tk.BooleanVar()
        ads_var.set(specie.flag_ads)
        ads_check = ttk.Checkbutton(sf_check_ads_des, variable=ads_var, 
                                    bootstyle="round-toggle", 
                                    onvalue=True, offvalue=False,
                                    command=self.toggle_ads_des)
        self.spe_entries["flag_ads"] = (ads_var, ads_check)
        ads_check.grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(sf_check_ads_des, text="Adsorption").grid(row=0, column=1, pady=5)
        des_var = tk.BooleanVar()
        des_var.set(specie.flag_des)
        des_check = ttk.Checkbutton(sf_check_ads_des, variable=des_var, 
                                    bootstyle="round-toggle", 
                                    onvalue=True, offvalue=False,
                                    command=self.toggle_ads_des)
        self.spe_entries["flag_des"] = (des_var, des_check)
        des_check.grid(row=0, column=2, padx=10, pady=5)
        ttk.Label(sf_check_ads_des, text="Desorption").grid(row=0, column=3, pady=5)

        ttk.Label(sf_entry_ads_des, text="Molecular mass").grid(row=0, column=0, padx=5, pady=5)
        mass_var = tk.StringVar()
        mass_var.set(specie.mass)
        mass_ety = ttk.Entry(sf_entry_ads_des, textvariable=mass_var, width=5)
        mass_ety.grid(row=0, column=1, padx=5, pady=5)
        self.spe_entries["mass"] = (mass_var, mass_ety)
        ttk.Label(sf_entry_ads_des, text="Parial pressure (%)").grid(row=0, column=2, padx=5, pady=5)
        pp_var = tk.StringVar()
        pp_var.set(specie.PP_ratio)
        pp_ety = ttk.Entry(sf_entry_ads_des, textvariable=pp_var, width=5)
        pp_ety.grid(row=0, column=3, padx=5, pady=5)
        self.spe_entries["PP_ratio"] = (pp_var, pp_ety)
        ttk.Label(sf_entry_ads_des, text="Gas Entropy (eV/K)").grid(row=0, column=4, padx=5, pady=5)
        S_var = tk.StringVar()
        S_var.set(specie.S_gas)
        S_ety = ttk.Entry(sf_entry_ads_des, textvariable=S_var, width=8)
        S_ety.grid(row=0, column=5, padx=5, pady=5)
        self.spe_entries["S_gas"] = (S_var, S_ety)

        ttk.Label(sf_entry_ads_des_2, 
                  text="Sticking coefficient (eV) -- on facets")\
                    .grid(row=0, column=0, padx=5, pady=1)
        S0_f_var = tk.StringVar()
        S0_f_var.set(specie.sticking[0])
        S0_f_ety = ttk.Entry(sf_entry_ads_des_2, textvariable=S0_f_var, width=5)
        S0_f_ety.grid(row=0, column=1, padx=5, pady=1)
        self.spe_entries["S0_f"] = (S0_f_var, S0_f_ety)
        ttk.Label(sf_entry_ads_des_2, text="-- on edges and corners")\
            .grid(row=0, column=2, padx=5, pady=1)
        S0_ce_var = tk.StringVar()
        S0_ce_var.set(specie.sticking[1])
        S0_ce_ety = ttk.Entry(sf_entry_ads_des_2, textvariable=S0_ce_var, width=5)
        S0_ce_ety.grid(row=0, column=3, padx=5, pady=1)
        self.spe_entries["S0_ce"] = (S0_ce_var, S0_ce_ety)

        self.toggle_ads_des()

        # Diff
        f_diff = tk.LabelFrame(master, bd=1)
        f_diff.grid(row=0, column=2, pady=5)
        sf_check_diff = ttk.Frame(f_diff)
        sf_entry_diff = ttk.Frame(f_diff)
        sf_check_diff.grid(row=0, column=0, pady = 5)
        sf_entry_diff.grid(row=1, column=0, pady = 5)
        diff_var = tk.BooleanVar()
        diff_var.set(specie.flag_diff)
        diff_check = ttk.Checkbutton(sf_check_diff, variable=diff_var, 
                                     bootstyle="round-toggle",
                                     onvalue=True, offvalue=False,
                                     command=self.toggle_diff)
        diff_check.grid(row=0, column=0, padx=5, pady=5)
        self.spe_entries["flag_diff"] = (diff_var, diff_check)
        ttk.Label(sf_check_diff, text="Diffusion").grid(row=0, column=1, pady=5)

        ttk.Label(sf_entry_diff, text="Diffusion barriar (eV)").grid(row=1, column=0, padx=5, pady=5)
        EaDiff_var = tk.StringVar()
        EaDiff_var.set(specie.Ea_diff)
        EaDiff_ety = ttk.Entry(sf_entry_diff, textvariable=EaDiff_var, width=5)
        EaDiff_ety.grid(row=1, column=1, padx=5, pady=8)
        ttk.Label(sf_entry_diff, text="  ").grid(row=2, column=0, pady=8)
        self.spe_entries["Ea_diff"] = (EaDiff_var, EaDiff_ety)

        self.toggle_diff()

        # gcn Scaling
        f_gcn = tk.LabelFrame(master, bd=1)
        f_gcn.grid(row=0, column=3, pady=5)
        sf_check_gcn = ttk.Frame(f_gcn)
        sf_entry_gcn = ttk.Frame(f_gcn)
        sf_check_gcn.grid(row=0, column=0, pady = 5)
        sf_entry_gcn.grid(row=1, column=0, pady = 5)
        twosite_var = tk.BooleanVar()
        twosite_var.set(specie.is_twosite)
        twosite_check = ttk.Checkbutton(sf_check_gcn, variable=twosite_var, 
                                        bootstyle="round-toggle",
                                        onvalue=True, offvalue=False,
                                        command=self.toggle_Sgcn)
        twosite_check.grid(row=0, column=0, padx=5, pady=5)
        self.spe_entries["is_twosite"] = (twosite_var, twosite_check)
        ttk.Label(sf_check_gcn, text="Two-site").grid(row=0, column=1, pady=5)

        ttk.Label(sf_entry_gcn, text="k@i").grid(row=1, column=0, padx=5, pady=5)
        Sgcn_ki_var = tk.StringVar()
        Sgcn_ki_var.set(specie.E_ads_para[0])
        Sgcn_ki_ety = ttk.Entry(sf_entry_gcn, textvariable=Sgcn_ki_var, width=5)
        Sgcn_ki_ety.grid(row=1, column=1, padx=5, pady=8)
        self.spe_entries["Sgcn_ki"] = (Sgcn_ki_var, Sgcn_ki_ety)
        ttk.Label(sf_entry_gcn, text="k@j").grid(row=1, column=2, padx=5, pady=5)
        Sgcn_kj_var = tk.StringVar()
        Sgcn_kj_var.set(specie.E_ads_para[1])
        Sgcn_kj_ety = ttk.Entry(sf_entry_gcn, textvariable=Sgcn_kj_var, width=5)
        Sgcn_kj_ety.grid(row=1, column=3, padx=5, pady=8)
        self.spe_entries["Sgcn_kj"] = (Sgcn_kj_var, Sgcn_kj_ety)
        ttk.Label(sf_entry_gcn, text="b").grid(row=1, column=4, padx=5, pady=5)
        Sgcn_b_var = tk.StringVar()
        Sgcn_b_var.set(specie.E_ads_para[2])
        Sgcn_b_ety = ttk.Entry(sf_entry_gcn, textvariable=Sgcn_b_var, width=5)
        Sgcn_b_ety.grid(row=1, column=5, padx=5, pady=8)
        self.spe_entries["Sgcn_b"] = (Sgcn_b_var, Sgcn_b_ety)
        ttk.Label(sf_entry_gcn, text="  ").grid(row=2, column=0, pady=8)

        self.toggle_Sgcn()

    def toggle_ads_des(self):
        f_ads = self.spe_entries["flag_ads"][0].get()
        f_des = self.spe_entries["flag_des"][0].get()
        if f_ads or f_des:
            self.spe_entries["mass"][1].config(state="normal")
            self.spe_entries["PP_ratio"][1].config(state="normal")
            self.spe_entries["S_gas"][1].config(state="normal")
            self.spe_entries["S0_f"][1].config(state="normal")
            self.spe_entries["S0_ce"][1].config(state="normal")
        else:
            self.spe_entries["mass"][1].config(state="disabled")
            self.spe_entries["PP_ratio"][1].config(state="disabled")
            self.spe_entries["S_gas"][1].config(state="disabled")
            self.spe_entries["S0_f"][1].config(state="disabled")
            self.spe_entries["S0_ce"][1].config(state="disabled")

    def toggle_diff(self):
        f_diff = self.spe_entries["flag_diff"][0].get()
        if f_diff:
            self.spe_entries["Ea_diff"][1].config(state="normal")
        else:
            self.spe_entries["Ea_diff"][1].config(state="disabled")

    def toggle_Sgcn(self):
        f_site = self.spe_entries["is_twosite"][0].get()
        if f_site:
            self.spe_entries["Sgcn_kj"][1].config(state="normal")
        else:
            self.spe_entries["Sgcn_kj"][1].config(state="disabled")


class Product_win(Scrollable_win):
    def __init__(self, window, label, products):
        super(Product_win, self).__init__(window)
        self.window.title("Products")
        self.window.geometry('')
        self.window.geometry('{}x{}+55+55'.format(int(self.width * 0.45), 
                                                  int(self.height * 0.45)))
        self.frame = tk.Frame(self.mainframe)
        self.frame.grid(row=0, column=1, padx=5, pady=5)
        self.products = products
        self.nproducts = len(products)
        self.label = label

        self.entries = []
        ttk.Label(self.mainframe, text="name")\
            .grid(row=0, column=0, padx=5, pady=5)
        for n, product in enumerate(self.products):
            var = ttk.StringVar()
            var.set(product.name)
            ety = ttk.Entry(self.frame, textvariable=var, width=8, justify="center")
            ety.grid(row=0, column=n + 1, padx=5, pady=5)
            self.entries.append((var, ety))
        bt_frame = tk.Frame(self.mainframe)
        bt_frame.grid(row=1, column=1, columnspan=5)
        add_button = ttk.Button(bt_frame, text="Add", 
                                bootstyle=(ttk.DARK, ttk.OUTLINE), 
                                width=7, command=self.__add)
        add_button.grid(row=1, column=0, padx=5, pady=5)
        del_button = ttk.Button(bt_frame, text="Delete", 
                                bootstyle=(ttk.DARK, ttk.OUTLINE), 
                                width=7, command=self.__delete)
        del_button.grid(row=1, column=1, padx=5, pady=5)
        save_button = ttk.Button(bt_frame, text="Save", 
                                bootstyle=(ttk.DARK, ttk.OUTLINE), 
                                width=7, command=self.__save)
        save_button.grid(row=1, column=2, padx=5, pady=5)
    
    def __add(self):
        newP = Product("")
        self.products.append(newP)
        self.nproducts += 1
        var = ttk.StringVar()
        var.set(newP.name)
        ety = ttk.Entry(self.frame, textvariable=var, width=8, justify="center")
        ety.grid(row=0, column=self.nproducts, padx=5, pady=5)
        self.entries.append((var, ety))

    def __delete(self):
        self.entries[-1][1].destroy()
        self.nproducts -= 1
        del self.entries[-1]
        del self.products[-1]

    def __save(self):
        for n, product in enumerate(self.products):
            product.name = self.entries[n][0].get()
        self.label.config(text = self.nproducts)
        self.window.destroy()


class Event_win(Scrollable_win):
    def __init__(self, window, label, events, products, react2id_map):
        super(Event_win, self).__init__(window)
        self.window.title("Events")
        self.window.geometry('{}x{}+55+55'.format(int(self.width * 0.75), 
                                                  int(self.height * 0.8)))
        self.frame = tk.Frame(self.mainframe)
        self.frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5)
        self.events = events
        self.nevents = len(events)
        self.label = label
        self.entries = [] # list of dicts
        self.rows = []
        self.products = products
        self.react2id_map = react2id_map
        self.id2react_map = dict((y,x) for x,y in react2id_map.items())
        self.__header()
        for n, evt in enumerate(self.events):
            self.__add_row(n, evt)
        add_button = ttk.Button(self.mainframe, text="Add", 
                                bootstyle=(ttk.DARK, ttk.OUTLINE), 
                                width=7, command=self.__add)
        add_button.grid(row=1, column=0, padx=5, pady=5)
        del_button = ttk.Button(self.mainframe, text="Delete", 
                                bootstyle=(ttk.DARK, ttk.OUTLINE), 
                                width=7, command=self.__delete)
        del_button.grid(row=1, column=1, padx=5, pady=5)
        save_button = ttk.Button(self.mainframe, text="Save", 
                                bootstyle=(ttk.DARK, ttk.OUTLINE), 
                                width=7, command=self.__save)
        save_button.grid(row=1, column=2, padx=5, pady=5)

    def __header(self):
        tk.Label(self.frame, text="name").grid(row=0, column=0, padx=8)
        tk.Label(self.frame, text="type").grid(row=0, column=1, padx=8)
        tk.Label(self.frame, text="two-site").grid(row=0, column=2, padx=8)
        tk.Label(self.frame, text="R@i").grid(row=0, column=3, padx=8)
        tk.Label(self.frame, text="R@j").grid(row=0, column=4, padx=8)
        tk.Label(self.frame, text="P@i").grid(row=0, column=5, padx=8)
        tk.Label(self.frame, text="P@j").grid(row=0, column=6, padx=8)
        tk.Label(self.frame, text="BEP_k").grid(row=0, column=7, padx=8)
        tk.Label(self.frame, text="BEP_b").grid(row=0, column=8, padx=8)

    def __add(self):
        newE = Event("")
        self.events.append(newE)
        self.nevents += 1
        self.__add_row(self.nevents, newE)

    def __add_row(self, n, event):
        row = Event_row(self.frame, n, event, self.id2react_map)
        self.rows.append(row)
        self.entries.append(row.evt_entries)
        # update rollabel region
        super().update_scroll_region()

    def __delete(self):
        if self.nevents > 1:
            # 由于控件绑定了函数，直接del无效
            # 手动调用__del__
            self.rows[-1].__del__() 
            del self.rows[-1]
            del self.events[-1]
            self.nevents -= 1
            # update rollabel region
            super().update_scroll_region()   

    def __save(self):
        for p in self.products:
            p.num_gen = 0
            p.event_gen = []
            p.num_consum = 0
            p.event_consum = []
        for n, evt in enumerate(self.events):
            evt_entries = self.entries[n]
            evt.name = evt_entries["name"][0].get()
            evt.type = evt_entries["type"][0].get()
            evt.is_twosite = evt_entries["is_twosite"][0].get()
            # R@i + P@i
            ri = self.react2id_map[evt_entries["Ri"][0].get()]
            if type(ri) == int:
                evt.cov_before[0] = ri
            else:
                evt.cov_before[0] = ri
                id = int(ri[1:])
                self.products[id-1].num_consum += 1
                self.products[id-1].event_consum.append(n+1)
            p_i = self.react2id_map[evt_entries["Pi"][0].get()]
            if type(p_i) == int:
                evt.cov_after[0] = p_i
            else:
                evt.cov_after[0] = p_i
                id = int(p_i[1:])
                self.products[id-1].num_gen += 1
                self.products[id-1].event_gen.append(n+1)
            # R@j + P@j
            if evt.is_twosite:
                rj = self.react2id_map[evt_entries["Rj"][0].get()]
                if type(rj) == int:
                    evt.cov_before[1] = rj
                else:
                    evt.cov_before[1] = rj
                    id = int(rj[1:])
                    self.products[id-1].num_consum += 1
                    self.products[id-1].event_consum.append(n+1)
                pj = self.react2id_map[evt_entries["Pj"][0].get()]
                if type(pj) == int:
                    evt.cov_after[1] = pj
                else:
                    evt.cov_after[1] = pj
                    id = int(pj[1:])
                    self.products[id-1].num_gen += 1
                    self.products[id-1].event_gen.append(n+1)
            # BEP realtion
            if evt.type == "Reaction":
                evt.BEP_para = [evt_entries["BEP_k"][0].get(),
                                evt_entries["BEP_b"][0].get()]
            # print(evt.__dict__)
            # print(evt_entries.keys())
        self.label.config(text = self.nevents)
        self.window.destroy()


class Event_row:
    def __init__(self, frame, nrow, event, id2react_map):
        self.evt_entries = {}
        react_list = list(id2react_map.values())
        n = nrow + 1

        name_var = tk.StringVar()
        name_var.set(event.name)
        name_entry = ttk.Entry(frame, textvariable=name_var, width=12, justify="center")
        name_entry.grid(row=n, column=0, padx=5, pady=5)
        self.evt_entries["name"] = (name_var, name_entry)

        type_var = tk.StringVar()
        type_var.trace_add("write", self.toggle_BEP)
        type_box = ttk.Combobox(frame, textvariable=type_var, 
                                justify="center", width=10,
                                values=["Adsorption", "Desorption", 
                                        "Diffusion", "Reaction"])
        type_box.config(state="readonly")
        self.evt_entries["type"] = (type_var, type_box)
        type_box.grid(row=n, column=1, padx=5, pady=5)

        flag_site = tk.BooleanVar()
        flag_site.set(event.is_twosite)
        site_check = ttk.Checkbutton(frame, variable=flag_site, 
                                     bootstyle="round-toggle", 
                                     onvalue=True, offvalue=False,
                                     command=self.toggle_site)
        site_check.grid(row=n, column=2, padx=5, pady=5)
        self.evt_entries["is_twosite"] = (flag_site, site_check)

        Ri_var = tk.StringVar()
        Ri_box = ttk.Combobox(frame, textvariable=Ri_var, 
                              justify="center", width=10,
                              values=react_list)
        Ri_box.config(state="readonly")
        if event.cov_before[0]:
            react = id2react_map[event.cov_before[0]]
            Ri_box.set(react)
        else:
            Ri_box.current(0)
        Ri_box.grid(row=n, column=3, padx=5, pady=5)
        self.evt_entries["Ri"] = (Ri_var, Ri_box)

        Rj_var = tk.StringVar()
        Rj_box = ttk.Combobox(frame, textvariable=Rj_var, 
                              justify="center", width=10,
                              values=react_list)
        Rj_box.config(state="readonly")
        if event.cov_before[1]:
            react = id2react_map[event.cov_before[0]]
            Rj_box.set(react)
        else:
            Rj_box.current(0)
        Rj_box.grid(row=n, column=4, padx=5, pady=5)
        self.evt_entries["Rj"] = (Rj_var, Rj_box)

        Pi_var = tk.StringVar()
        Pi_box = ttk.Combobox(frame, textvariable=Pi_var, 
                              justify="center", width=10,
                              values=react_list)
        Pi_box.config(state="readonly")
        if event.cov_after[0]:
            react = id2react_map[event.cov_after[0]]
            Pi_box.set(react)
        else:
            Pi_box.current(0)
        Pi_box.grid(row=n, column=5, padx=5, pady=5)
        self.evt_entries["Pi"] = (Pi_var, Pi_box)

        Pj_var = tk.StringVar()
        Pj_box = ttk.Combobox(frame, textvariable=Pj_var, 
                              justify="center", width=10,
                              values=react_list)
        Pj_box.config(state="readonly")
        if event.cov_after[1]:
            react = id2react_map[event.cov_after[1]]
            Pj_box.set(react)
        else:
            Pj_box.current(0)
        Pj_box.grid(row=n, column=6, padx=5, pady=5)
        self.evt_entries["Pj"] = (Pj_var, Pj_box)

        self.toggle_site()

        BEP_k_var = tk.StringVar()
        BEP_k_var.set(event.BEP_para[0])
        BEP_k_entry = ttk.Entry(frame, textvariable=BEP_k_var, width=12, justify="center")
        BEP_k_entry.grid(row=n, column=7, padx=5, pady=5)
        self.evt_entries["BEP_k"] = (BEP_k_var, BEP_k_entry)

        BEP_b_var = tk.StringVar()
        BEP_b_var.set(event.BEP_para[1])
        BEP_b_entry = ttk.Entry(frame, textvariable=BEP_b_var, width=12, justify="center")
        BEP_b_entry.grid(row=n, column=8, padx=5, pady=5)
        self.evt_entries["BEP_b"] = (BEP_b_var, BEP_b_entry)

        # set type here to aviod KeyError
        if event.type:
            type_var.set(event.type)
        else:
            type_box.current(0)
    
    def toggle_site(self):
        f_site = self.evt_entries["is_twosite"][0].get()
        if f_site:
            self.evt_entries["Rj"][1].config(state="normal")
            self.evt_entries["Pj"][1].config(state="normal")
        else:
            self.evt_entries["Rj"][1].config(state="disabled")
            self.evt_entries["Pj"][1].config(state="disabled")

    def toggle_BEP(self, *args):
        e_type = self.evt_entries["type"][0].get()
        if e_type == "Reaction":
            self.evt_entries["BEP_k"][1].config(state="normal")
            self.evt_entries["BEP_b"][1].config(state="normal")
        else:
            self.evt_entries["BEP_k"][1].config(state="disabled")
            self.evt_entries["BEP_b"][1].config(state="disabled")
    
    def __del__(self):
        for _, entries in self.evt_entries.items():
            entries[1].destroy()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
    root = tk.Tk()
    face_header = [
        "Index", "Surface energy(eV)", "Adsorption Energy(eV)",
        "Adsorption Entropy(eV/K)", "Lateral interaction(eV)"
    ]
    items = ["index", "gamma", "E_ads", "S_ads", "w"]
    face_frame = FacesFrame(root, face_header, items)
    face_frame.pack()
    button1 = tk.Button(root, text='save', width=10, bd=5,
                        command=face_frame.save_frame_entry)
    button1.pack()
    button2 = tk.Button(root, text='load', width=10, bd=5,
                        command=face_frame.read_frame_entry)
    button2.pack()
    kmc_frame = KmcFrame(root)
    kmc_frame.pack()
    root.mainloop()
