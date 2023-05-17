# -*- coding: utf-8 -*-
"""
@author: yinglei
"""

import tkinter as tk
import ttkbootstrap as ttk
import win32api
import warnings
import os
import sys
from tkinter.messagebox import askyesno
from customization import Customization


def handle_warning(message, category, filename, lineno, file=None, line=None):
    q = 'A warning occurred:\n"' + str(message) + '"\nDo you wish to continue?'
    response = askyesno(title='Warnings', message=q)

    if not response:
        raise category(message)


class App:
    def __init__(self, master):
        self.master = master
        self.master.option_add("*Font", ("Arial", 10))
        self.master.title('Multiscale Operando Simulation Package')
        # Get the system metrics to set screen
        height = win32api.GetSystemMetrics(1)
        width = win32api.GetSystemMetrics(0)
        self.master.geometry('{}x{}+50+50'.format(int(width * 0.85), int(height * 0.8)))

        # Create rollable canvas
        self.canvas = tk.Canvas(self.master, bg='#f0f0f0')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        mainframe = tk.Frame(self.canvas)

        # Create tab
        tabControl = ttk.Notebook(mainframe)  # Create Tab Control
        tab0 = ttk.Frame(tabControl)  # Add a tab
        tabControl.add(tab0, text=' MSRM ')  # Make tab visible
        tabControl.pack(expand=1, fill="both")  # Pack to make visible

        Customization(tab0, mainframe, self.canvas)

        # Set rollabel region
        self.canvas.create_window(0, 0, anchor=tk.NW, window=mainframe)
        mainframe.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        # Create Scrollbars and relate them to Canvas
        hscrollbar = tk.Scrollbar(self.master,
                                  orient=tk.HORIZONTAL,
                                  command=self.canvas.xview)
        vscrollbar = tk.Scrollbar(self.master,
                                  orient=tk.VERTICAL,
                                  command=self.canvas.yview)
        # bind wheel to vscrollbar if focus
        mainframe.bind('<Enter>', self._bound_to_mousewheel)
        mainframe.bind('<Leave>', self._unbound_to_mousewheel)
        self.canvas.configure(xscrollcommand=hscrollbar.set,
                              yscrollcommand=vscrollbar.set)
        # Set location of canvas and scrollbars
        self.canvas.pack(fill=tk.BOTH, expand=True)
        hscrollbar.place(relx=0, rely=1.0, relwidth=1.0, anchor=tk.SW)
        vscrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor=tk.NE)

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


if __name__ == '__main__':
    warnings.showwarning = handle_warning
    # Change the current directory to the directory of the given script
    pwd0 = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(pwd0)
    # Create window
    window = ttk.Window(themename="litera")
    # Set logo
    direc_tory = os.path.abspath('logo.ico')
    window.iconbitmap(direc_tory)
    # Change directory to record data
    os.chdir(os.path.join(pwd0, 'data'))
    app = App(window)
    window.mainloop()
