# -*- coding: utf-8 -*-
"""
@author: yinglei
"""

import json
import time
import os
import tkinter as tk
import ttkbootstrap as ttk
from tkinter.filedialog import asksaveasfilename, askopenfilename
from tkinter.messagebox import showinfo, askyesno
from mosp_frame import FacesFrame, KmcFrame
from func.Custom_msr import Wulff
from func.wx_opengl import glwindow
from func.wx_plt import kmc_window

class Customization:
    def __init__(self, master, scrollframe=None, scrollcanvas=None):
        self.master = master
        self.entries = {}
        self.values = {}
        self.center = tk.W + tk.E + tk.S + tk.N

        # Create Subframes
        self.__Create_Input()
        self.__Create_Gases()
        self.__Create_Faces(scrollframe, scrollcanvas)
        self.__Create_Func()

        self.__Create_kmc()

    def __Create_widget(self, window, key, type, boxvalues=None):
        var = tk.StringVar()
        if type == 'Entry':
            widget = ttk.Entry(window, textvariable=var, width=12, justify="center")
        if type == 'Combobox':
            widget = ttk.Combobox(window, textvariable=var, justify="center",
                                  values=boxvalues, width=10)
            widget.config(state="readonly")
            widget.current(0)
        self.entries[key] = var, widget
        return widget

    def __Create_Input(self):
        Input = tk.LabelFrame(self.master, text=' MSR ', font=("Arial", 12), bd=2)
        Input.grid(row=0, column=0, sticky=self.center)
        items1 = [("Element", '', 'Entry', ''),
                  ("Lattice constant", '(\u00C5)', 'Entry', ''),
                  ("Crystal structure", '', 'Combobox', ('FCC', 'BCC'))]
        items2 = [("Pressure", '(Pa)', 'Entry', ''), ("Temperature", '(K)', 'Entry', ''),
                  ("Radius", '(\u00C5)', 'Entry', '')]
        # Subframe-Input
        for i, (label, unit, widget_type, boxvalues) in enumerate(items1):
            Row_N = 0
            tk.Label(Input, text=label+unit)\
                .grid(row=Row_N, column=2*i, padx=5, pady=5, sticky=tk.W)
            entry = self.__Create_widget(Input, label, widget_type, boxvalues)
            entry.grid(row=Row_N, column=2 * i + 1, padx=5, pady=5)
        for i, (label, unit, widget_type, boxvalues) in enumerate(items2):
            Row_N = 1
            tk.Label(Input, text=label+unit)\
                .grid(row=Row_N, column=2*i, padx=5, pady=5, sticky=tk.W)
            entry = self.__Create_widget(Input, label, widget_type, boxvalues)
            entry.grid(row=Row_N, column=2 * i + 1, padx=5, pady=5)

    def __Create_Gases(self):
        Gases = tk.LabelFrame(self.master, bd=2)
        Gases.grid(row=1, column=0, sticky=self.center)
        gases = ["Gas1", "Gas2", "Gas3"]
        items = ["name", "pp", "S", "type"]
        gas_widgets = []
        for gas in gases:
            gas_widgets.append([])
            for item in items:
                name = f"{gas}_{item}"
                if item != 'type':
                    widget = self.__Create_widget(Gases, name, 'Entry')
                else:
                    widget = self.__Create_widget(Gases, name, 'Combobox',
                                                  boxvalues=('Associative',
                                                             'Dissociative'))
                gas_widgets[-1].append(widget)

        gas_header = [
            "Name", "Partial Pressure(%)", "Gas Entropy(eV/T)", "Adsorption type"
        ]
        for i, item in enumerate(gas_header):
            tk.Label(Gases, text=item)\
                .grid(row=0, column=i+1, padx=10, pady=5, sticky=tk.W+tk.E)

        for i, gas in enumerate(gases):
            tk.Label(Gases, text=gas)\
                .grid(row=i+1, column=0, padx=10, pady=5, sticky=tk.W+tk.E)
            for j, widget in enumerate(gas_widgets[i]):
                widget.grid(row=i + 1, column=j + 1, padx=10, pady=5)

    def __Create_Faces(self, scrollframe, scrollcanvas):
        Faces = tk.LabelFrame(self.master, bd=2)
        Faces.grid(row=2, column=0, sticky=self.center)
        # Subframe-Faces
        face_header = [
            "Index", "Surface energy(eV/\u00C5²)", "E_ads(eV)", "S_ads(eV/T)",
            "Lateral interaction(eV)"
        ]
        items = ["index", "gamma", "E_ads", "S_ads", "w"]
        self.face_frame = FacesFrame(Faces, face_header, items, 3, scrollframe,
                                     scrollcanvas)
        self.face_frame.grid(row=0)

    def __Create_Func(self):
        Func = tk.LabelFrame(self.master)
        Func.grid(row=3, column=0, sticky=self.center)
        load_button = ttk.Button(Func,
                                 text='Load',
                                 width=10,
                                 command=self.read_entries,
                                 bootstyle=(ttk.DARK, ttk.OUTLINE))
        load_button.grid(row=0, column=0, padx=30, pady=15, sticky=self.center)
        save_button = ttk.Button(Func,
                                 text='Save',
                                 width=10,
                                 command=self.save_entry,
                                 bootstyle=(ttk.DARK, ttk.OUTLINE))
        save_button.grid(row=0, column=1, padx=30, pady=15, sticky=self.center)
        run_button = ttk.Button(Func,
                                text='run',
                                width=10,
                                command=self.run_msr,
                                bootstyle=(ttk.DARK, ttk.OUTLINE))
        run_button.grid(row=0, column=2, padx=30, pady=15, sticky=self.center)

    def __Create_kmc(self):
        Kmc_ = tk.LabelFrame(self.master, text=' KMC ', font=("Arial", 12), bd=2)
        Kmc_.grid(row=0, column=1, rowspan=3, sticky=self.center)
        self.kmc_frame = KmcFrame(Kmc_)
        self.kmc_frame.grid(row=0)
        kmc_func = tk.LabelFrame(self.master)
        kmc_func.grid(row=3, column=1, sticky=self.center)
        load_button = ttk.Button(kmc_func,
                                 text='Load',
                                 width=10,
                                 command=self.kmc_frame.read_entries,
                                 bootstyle=(ttk.DARK, ttk.OUTLINE))
        load_button.grid(row=0, column=0, padx=30, pady=15, sticky=self.center)
        save_button = ttk.Button(kmc_func,
                                 text='Save',
                                 width=10,
                                 command=self.kmc_frame.save_entery,
                                 bootstyle=(ttk.DARK, ttk.OUTLINE))
        save_button.grid(row=0, column=1, padx=30, pady=15, sticky=self.center)
        run_button = ttk.Button(kmc_func,
                                text='run',
                                width=10,
                                command=self.run_kmc,
                                bootstyle=(ttk.DARK, ttk.OUTLINE))
        run_button.grid(row=0, column=2, padx=30, pady=15, sticky=self.center)

    def get_entries(self):
        # retrieve the values form Tkinter-var and store in dict
        # values in face_frame are called independently
        for name, (var, _) in self.entries.items():
            self.values[name] = var.get()
        frame_values = self.face_frame.save_frame_entry()
        self.values.update(frame_values)

    def read_entries(self):
        # read values from the selected file in JSON format
        # update the corresponding Tkinter-var
        # values in face_frame are update indenpendently
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
        self.values.update(self.face_frame.read_frame_entry(frame_values))

    def save_entry(self):
        # save the data in a user-defined file
        self.get_entries()
        filename = asksaveasfilename(defaultextension='.txt')
        if not filename:
            return
        with open(filename, 'w') as f:
            json.dump(self.values, f, indent=2)
        showinfo("Save", "Inputs have been saved")

    def run_msr(self):
        sj_start = time.time()

        self.get_entries()
        wulff = Wulff()
        wulff.get_para(self.values)
        wulff.gen_coverage()
        flag = wulff.geometry()
        if flag:
            sj_elapsed = round(time.time() - sj_start, 4)
            q = 'MSR Job Completed. Total Cost About: ' + str(sj_elapsed) + ' Seconds\n'\
                + 'Visulize the NanoParticles?'
            response = askyesno(title='Visualized?', message=q)
            if response:
                size = float(self.values['Radius']) + 15.0
                glwindow('ini.xyz', size)
            else:
                pass

    def run_kmc(self):
        sj_start = time.time()

        self.get_entries()
        kmc_valuse = self.kmc_frame.get_entries()
        with open('kmc_input.txt', 'w') as f:
            f.write('0\n')
            f.write(f"{kmc_valuse['nLoop']}\t{kmc_valuse['record_int']}\n")
            f.write(f"{kmc_valuse['dim_x']}\t{kmc_valuse['dim_y']}\t{kmc_valuse['dim_z']}\n")
            f.write(f"{kmc_valuse['S0_Gas1_edge']}\t{kmc_valuse['S0_Gas1_face']}\n")
            f.write(f"{kmc_valuse['S0_Gas2_edge']}\t{kmc_valuse['S0_Gas2_face']}\n")
            f.write(f"{kmc_valuse['Ediff_gas1']}\t{kmc_valuse['Ediff_gas2']}\n")
            f.write(f"{kmc_valuse['Eads_Gas1_a']}\t{kmc_valuse['Eads_Gas1_b']}\n")
            f.write(f"{kmc_valuse['Eads_Gas2_a']}\t{kmc_valuse['Eads_Gas2_b']}\n")
            f.write(f"{kmc_valuse['BEP_a']}\t{kmc_valuse['BEP_b']}\n")
            f.write('\n')
            f.write(f"{self.values['Element']}\n")
            f.write(f"{self.values['Lattice constant']}\n")
            f.write(f"{self.values['Temperature']}\t{self.values['Pressure']}\n")
            f.write(f"0.{self.values['Gas1_pp']}\t0.{self.values['Gas2_pp']}\n")
            f.write(f"{self.values['Gas1_S']}\t{self.values['Gas2_S']}\n")
            f.write(f"{kmc_valuse['E_gas1-gas1']}\t{kmc_valuse['E_gas1-gas2']}\t{kmc_valuse['E_gas2-gas2']}\n")

        os.system("del *.dat* atom_str*.xyz")
        os.system("main.exe")
        sj_elapsed = round(time.time() - sj_start, 4)
        q = 'KMC Job Completed. Total Cost About: ' + str(sj_elapsed) + ' Seconds\n'\
            + 'Analyze the kmc results?'
        response = askyesno(title='Analyze?', message=q)
        if response:
            nloop = int(kmc_valuse['nLoop'])
            inteval = int(kmc_valuse['record_int'])
            inteval = int(nloop//inteval/10)*inteval
            size = float(self.values['Radius']) + 15.0
            kmc_window(inteval = inteval, glsize=size)
        else:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    Customization(root)
    root.mainloop()
