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
        self.entries = []
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
            self.textboxes = self.textboxes[:-1]
            self.entries = self.entries[:-1]
            self.parententries = self.parententries[:-1]
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


class KmcFrame(tk.Frame):
    def __init__(self, parent,):
        tk.Frame.__init__(self, parent)
        self.entries = {}
        self.values = {}
        self.center = tk.W + tk.E + tk.S + tk.N
        # initial structure set
        f_struct = tk.Frame(self)
        self.__create_f_struct(f_struct)
        f_struct.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        # record
        f_record = tk.Frame(self)
        self.__create_f_record(f_record)
        f_record.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        # species
        f_species = tk.Frame(self)
        f_species.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        # lateral interaction
        f_lat = tk.Frame(self)
        self.__create_f_lat(f_lat)
        f_lat.grid(row=7, column=0, padx=5, sticky=tk.W)

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

    def __create_f_lat(self, frame):
        tk.Label(frame, text="Average lateral interaciont(eV):")\
            .grid(row=0, column=0, pady=5, sticky=tk.W)     

    def __read_struct_path(self):
        self.stru_filename = askopenfilename(title="Select the initial structure file", \
                                             filetypes=(("xyz files", "*.xyz"),))
        if not self.stru_filename:
            self.stru_var.set(0)
            return


    def get_entries(self):
        for name, (var, _) in self.entries.items():
            self.values[name] = var.get()
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


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
    root = tk.Tk()
    face_header = [
        "Index", "Surface energy(eV)", "Adsorption Energy(eV)",
        "Adsorption Entropy(eV/T)", "Lateral interaction(eV)"
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
