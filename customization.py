# -*- coding: utf-8 -*-
"""
@author: yinglei
"""

import json
import time
import os
import tkinter as tk
import ttkbootstrap as ttk
import numpy as np
from tkinter.filedialog import asksaveasfilename, askopenfilename
from tkinter.messagebox import showinfo, askyesno
from views.mosp_frame import FacesFrame, KmcFrame
from utils.Custom_msr import Wulff
from utils.wx_opengl import glwindow
from utils.wx_plt import kmc_window

class Customization:
    def __init__(self, master, scrollframe=None, scrollcanvas=None):
        self.master = master
        self.entries = {}
        self.values = {}
        self.center = tk.W + tk.E + tk.S + tk.N

        # Create Subframes
        f_input = tk.LabelFrame(self.master, text=' MSR ', font=("Arial", 12), bd=2)
        f_input.grid(row=0, column=0, sticky=self.center)
        self.__Create_Input(f_input)
        f_gases = tk.LabelFrame(self.master, bd=2)
        f_gases.grid(row=1, column=0, sticky=self.center)
        self.__Create_Gases(f_gases)
        f_faces = tk.LabelFrame(self.master, bd=2)
        f_faces.grid(row=2, column=0, sticky=self.center)
        self.__Create_Faces(f_faces, scrollframe, scrollcanvas)

        self.__Create_Func_msr()

        f_kmc = tk.LabelFrame(self.master, text=' KMC ', font=("Arial", 12), bd=2)
        f_kmc.grid(row=0, column=1, rowspan=3, sticky=self.center)
        self.kmc_frame = KmcFrame(f_kmc)
        self.kmc_frame.grid(row=0)
        self.__Create_Func_kmc()

        # trace changes of gases-related inputs
        '''for gas_i in ["Gas1", "Gas2", "Gas3"]:
            for item in ["name", "pp", "S", "type"]:
                var, _ = self.entries[f"{gas_i}_{item}"]
                var.trace_add("write", self.__update_n_in_kmc)'''

    # def __update_n_in_kmc(self, *args):
    def __update_n_in_kmc(self):
        # trace changes of gases
        # change nSpecies and initaite Species in kmc_frame
        count = 0
        spe_list = []
        Sgas_list = []
        pp_list = []
        type_list =[]
        for key in ["Gas1", "Gas2", "Gas3"]:
            var, _ = self.entries[key+"_name"]
            name = var.get()
            if name:
                var, _ = self.entries[key+"_S"] 
                Sgas_list.append(var.get())
                var, _ = self.entries[key+"_pp"]
                pp_list.append(var.get())
                count += 1
                var, _ = self.entries[key+"_type"]
                type_list.append(var.get())
                spe_list.append(name)
                
        self.kmc_frame.ini_specie(count, spe_list, Sgas_list, pp_list, type_list)

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

    def __Create_Input(self, Input):
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

    def __Create_Gases(self, Gases):
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
            "Name", "Partial Pressure(%)", "Gas Entropy(eV/K)", "Adsorption type"
        ]
        for i, item in enumerate(gas_header):
            tk.Label(Gases, text=item)\
                .grid(row=0, column=i+1, padx=10, pady=5, sticky=tk.W+tk.E)

        for i, gas in enumerate(gases):
            tk.Label(Gases, text=gas)\
                .grid(row=i+1, column=0, padx=10, pady=5, sticky=tk.W+tk.E)
            for j, widget in enumerate(gas_widgets[i]):
                widget.grid(row=i + 1, column=j + 1, padx=10, pady=5)

        update_btn = ttk.Button(Gases, text="Update \n in kmc", width=8,
                                command=self.__update_n_in_kmc,
                                bootstyle=(ttk.DARK, ttk.OUTLINE))
        update_btn.grid(row=2, column=6, rowspan=2, padx=30, pady=5)

    def __Create_Faces(self, Faces, scrollframe, scrollcanvas):
        # Subframe-Faces
        face_header = [
            "Index", "Surface energy(eV/\u00C5²)", "E_ads(eV)", "S_ads(eV/K)",
            "Lateral interaction(eV)"
        ]
        items = ["index", "gamma", "E_ads", "S_ads", "w"]
        self.face_frame = FacesFrame(Faces, face_header, items, 3, scrollframe,
                                     scrollcanvas)
        self.face_frame.grid(row=0)

    def __Create_Func_msr(self):
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
        # add becasuse of scrollbar
        tk.Label(Func, text=" ").grid(row=1, column=0, padx=10)

    def __Create_Func_kmc(self):
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
        # add becasuse of scrollbar
        tk.Label(kmc_func, text=" ").grid(row=1, column=0, padx=10)

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
                glwindow('INPUT/ini.xyz', size)
            else:
                pass

    def run_kmc(self):
        sj_start = time.time()

        self.get_entries()
        if self.values['Crystal structure'] == 'FCC':
            bond_length = 1.45/2*float(self.values['Lattice constant'])
        elif self.values['Crystal structure'] == 'BCC':
            bond_length = 1.75/2*float(self.values['Lattice constant'])
        bond_length = (int(bond_length*10) + 1)/10.0

        kmc_values = self.kmc_frame.get_entries()
        with open('INPUT/input.txt', 'w') as f_ini:
            f_ini.write(f"{self.values['Temperature']}\t\t ! Temperature (K)\n")
            f_ini.write(f"{self.values['Pressure']}\t\t ! Pressure (Pa)\n")
            f_ini.write(f"{bond_length}\t\t ! Bond length (A)\n")
            f_ini.write(f"{kmc_values['nspecies']}\t\t ! Num of species\n")
            f_ini.write(f"{kmc_values['nevents']}\t\t ! Num of events\n")
            f_ini.write(f"{kmc_values['nproducts']}\t\t ! Num of products\n")
            f_ini.write(f"{kmc_values['nLoop']}\t\t ! Num of steps\n")
            f_ini.write(f"{kmc_values['record_int']}\t\t ! record inteval\n")

        li = np.array(kmc_values["li"])
        li = li.astype(np.float32)
        np.savetxt("INPUT/li.txt", li, fmt="%.3f", delimiter="\t")

        with open('INPUT/species.txt', 'w') as s_ini:
            for n in range(kmc_values['nspecies']): 
                spe_dict = json.loads(kmc_values[f"s{n}"])
                # again: note that ID is starting from 1
                s_ini.write(f"ID: {n+1}\n")
                s_ini.write(f"Name: {spe_dict['name']}\n")
                s_ini.write(f"is_twosite: {spe_dict['is_twosite']}\n")
                s_ini.write(f"mass: {spe_dict['mass']}\n")
                s_ini.write(f"S_gas: {spe_dict['S_gas']}\n")
                s_ini.write(f"sticking: {spe_dict['sticking'][0]} {spe_dict['sticking'][1]}\n")
                s_ini.write(f"E_ads_para: {spe_dict['E_ads_para'][0]} {spe_dict['E_ads_para'][1]} {spe_dict['E_ads_para'][2]}\n")
                s_ini.write(f"Ea_diff: {spe_dict['Ea_diff']}\n")
                s_ini.write(f"PP_ratio: {float(spe_dict['PP_ratio'])*0.01}\n")
                s_ini.write(f"\n")
        
        with open('INPUT/products.txt', 'w') as p_ini:
            for n in range(kmc_values['nproducts']):
                pro_dict = json.loads(kmc_values[f"p{n}"])
                p_ini.write(f"ID: {n+1}\n")
                p_ini.write(f"Name: {pro_dict['name']}\n")
                p_ini.write(f"num_gen: {pro_dict['num_gen']}\n")
                p_ini.write(f"event_gen: ")
                if pro_dict['num_gen']:
                    for i in range(pro_dict['num_gen']):
                        p_ini.write(f"{pro_dict['event_gen'][i]} ")
                    p_ini.write("\n")
                else:
                    p_ini.write("0\n")
                p_ini.write(f"num_consum: {pro_dict['num_consum']}\n")
                p_ini.write(f"event_consum: ")
                if pro_dict['num_consum']:
                    for i in range(pro_dict['num_consum']):
                        p_ini.write(f"{pro_dict['event_consum'][i]} ")
                    p_ini.write("\n")
                else:
                    p_ini.write("0\n")
                p_ini.write("\n")
                
        type_alias = {"Adsorption": "ads", "Desorption": "des", 
                     "Diffusion": "diff", "Reaction": "diff"}
        with open('INPUT/events.txt', 'w') as e_ini:
            for n in range(kmc_values['nevents']): 
                evt_dict = json.loads(kmc_values[f"e{n}"])
                # again: note that ID is starting from 1
                e_ini.write(f"ID: {n+1}\n")
                e_ini.write(f"Name: {evt_dict['name']}\n")
                e_ini.write(f"event_type: {type_alias[evt_dict['type']]}\n")
                e_ini.write(f"is_twosite: {evt_dict['is_twosite']}\n")
                e_ini.write("cov_before: " 
                            + f"{self.__id2cov(evt_dict['cov_before'][0])} "
                            + f"{self.__id2cov(evt_dict['cov_before'][1])}\n")
                e_ini.write("cov_after: " 
                            + f"{self.__id2cov(evt_dict['cov_after'][0])} "
                            + f"{self.__id2cov(evt_dict['cov_after'][1])}\n")
                if evt_dict['type'] == 'Reaction':
                    e_ini.write(f"BEP_para: {evt_dict['BEP_para'][0]} "
                                + f"{evt_dict['BEP_para'][0]}\n")
                e_ini.write("\n")

        '''os.system("del *.dat* atom_str*.xyz")
        if response:
            nloop = int(kmc_values['nLoop'])
            inteval = int(kmc_values['record_int'])
            inteval = int(nloop//inteval/10)*inteval
            size = float(self.values['Radius']) + 15.0
            kmc_window(inteval = inteval, glsize=size)
        else:
            pass'''
        
        os.system("main.exe")
        sj_elapsed = round(time.time() - sj_start, 4)
        q = 'KMC Job Completed. Total Cost About: ' + str(sj_elapsed) + ' Seconds\n'\
            + 'Analyze the kmc results?'
        response = askyesno(title='Analyze?', message=q)
    
    @staticmethod
    def __id2cov(id):
        if type(id) == int:
            return id
        else:
            return 0

if __name__ == "__main__":
    root = tk.Tk()
    Customization(root)
    root.mainloop()
