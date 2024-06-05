# -*- coding: utf-8 -*-
"""
@author: yinglei
"""

import numpy as np
from matplotlib import cm
from matplotlib.colors import ListedColormap

ELE_COLORS = {
    'H': (1.00, 1.00, 1.00),
    'He': (0.80, 0.80, 0.80),
    'Li': (0.851, 1.00, 1.00),
    'Be': (0.761, 1.0, 1.00),
    'B': (1.00, 0.71, 0.71),
    'C': (0.565, 0.565, 0.565),
    'N': (0.188, 0.314, 0.973),
    'O': (1.00, 0.051, 0.051),
    'F': (0.565, 0.878, 0.314),
    'Na': (0.671, 0.361, 0.949),
    'Mg': (0.541, 1.00, 0.00),
    'Al': (0.749, 0.651, 0.651),
    'Si': (0.941, 0.784, 0.627),
    'P': (1.00, 0.502, 0.00),
    'S': (1.00, 1.00, 0.188),
    'Fe': (0.878, 0.400, 0.200),
    'Co': (0.242, 0.242, 0.242),
    'Ni': (0.314, 0.816, 0.314),
    'Cu': (0.784, 0.502, 0.200),
    'Zn': (0.490, 0.502, 0.690),
    'Pd': (0.000, 0.412, 0.522),
    'Ag': (0.753, 0.753, 0.753),
    'Ce': (1.00, 1.00, 0.78),
    'Pt': (0.816, 0.816, 0.878),
    'Au': (0.996, 0.698, 0.2196),
    }

TYPE_COLORS = {
    '100': (0.557, 0.714, 0.611),
    '110': (0.851, 0.310, 0.200),
    '111': (0.565, 0.745, 0.878),
    'edge': (0.816, 0.816, 0.878),
    'corner': (0.933, 0.749, 0.427),
    'subsurface': (1.00, 0.78, 0.78),
    'bulk': (0.008, 0.188, 0.200)
    }

TOF_CM = cm.YlOrBr_r
GCN_CM = ListedColormap(
    [[0.98039216, 0.93333333, 0.80784314, 1.        ],
     [0.94509804, 0.96470588, 0.95686275, 1.        ],
     [0.63921569, 0.8       , 0.96078431, 1.        ],
     [0.39215686, 0.51372549, 0.63529412, 1.        ],
     [0.34      , 0.38      , 0.42      , 1.        ],
     [0.20392157, 0.25490196, 0.30588235, 1.        ]])

def get_ele_color(element):
    return ELE_COLORS.get(element, (1.00, 0.08, 0.576))

def get_type_color(type):
    return TYPE_COLORS.get(type, (0.816, 0.816, 0.878))


class NanoParticle:
    def __init__(self, eles, positions, siteTypes=None, covTypes=None):
        self.colorlist = []
        if isinstance(eles, str):
            self.eles = [eles for i in range(len(positions))]
        else:
            self.eles = np.array(eles)
        self.positions = np.array(positions)
        self.siteTypes = np.array(siteTypes)
        self.covTypes = np.array(covTypes)
        self.colors = np.zeros((len(self.eles), 3))
        self.nAtoms = len(self.eles)
        self.maxZ = np.max(self.positions, axis=0)[2]
        self.TOFs = {}
        self.TOFcolors = {}
        if not siteTypes is None:
            self.colorlist.append("site_type")
        self.colorlist.append("element")

    def setColors(self, coltype):
        self.coltype = coltype
        if coltype == 'element':
            for i, ele in enumerate(self.eles):
                self.colors[i] = get_ele_color(ele)
        elif coltype == 'site_type':
            for i, type in enumerate(self.siteTypes):
                type = type.strip()
                self.colors[i] = get_type_color(type)
        elif coltype == 'GCN':
            self.colors = self.gcnColors.copy()
        else:
            if self.TOFcolors.get(coltype):
                self.colors = self.TOFcolors[coltype].copy()
    
    def addColorGCN(self, GCNs):
        GCNs = np.array(GCNs)
        min = GCNs.min()
        if min > 3:
            min = 3
        self.gcnColors = [GCN_CM((float(gcn)-3) / (12-min)) for gcn in GCNs]
        self.GCNs = GCNs
        if "GCN" not in self.colorlist:
            self.colorlist.append("GCN")

    def addColorTOF(self, name, TOFs):
        TOFs = np.array(TOFs)
        max = TOFs.max()
        if (max > 0):
            normalTOFs = np.interp(TOFs, (0, max), (0, 1))
        else:
            normalTOFs = TOFs
        self.TOFcolors[f"TOF({name})"] \
            = [TOF_CM(tof[0]) for tof in normalTOFs]
        self.TOFs[f"TOF({name})"] = normalTOFs
        if f"TOF({name})" not in self.colorlist:
            self.colorlist.append(f"TOF({name})")
    
