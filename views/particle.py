# -*- coding: utf-8 -*-
"""
@author: yinglei
"""

import numpy as np

def get_color(element):
    colors = {
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
        'Co': (0.941, 0.565, 0.627),
        'Ni': (0.314, 0.816, 0.314),
        'Cu': (0.784, 0.502, 0.200),
        'Zn': (0.490, 0.502, 0.690),
        'Pd': (0.000, 0.412, 0.522),
        'Ag': (0.753, 0.753, 0.753),
        'Ce': (1.00, 1.00, 0.78),
        'Pt': (0.816, 0.816, 0.878),
        'Au': (0.996, 0.698, 0.2196),
    }
    return colors.get(element, (1.00, 0.08, 0.576))


class NanoParticle:
    def __init__(self, eles, positions, siteTypes=None, covTypes=None, TOFs=None):
        self.eles = np.array(eles)
        self.positions = np.array(positions)
        self.siteTypes = np.array(siteTypes)
        self.covTypes = np.array(covTypes)
        self.TOFs = np.array(TOFs)
        self.colors = np.zeros((len(self.eles), 3))
        self.maxZ = np.max(self.positions, axis=0)[2]

    def setColors(self, coltype):
        for i, ele in enumerate(self.eles):
            col = get_color(ele)
            self.colors[i] = col
