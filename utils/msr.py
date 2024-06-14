# -*- coding: utf-8 -*-
"""
@author: yinglei
"""

import re
from scipy.optimize import fsolve
from functools import reduce
from itertools import permutations
import warnings
import numpy as np
import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
R = 8.314
P0 = 100000
unit_coversion = 0.0000103643
k_b = 0.000086173303


# pause if warning
def handle_warning(message, category, filename, lineno, file=None, line=None):
    pass


def hcf(x, y):
    """Return the greatest common divisor of two numbers."""
    if x == 0:
        return y
    elif y == 0:
        return x

    # Apply Euclidean algorithm
    while y != 0:
        x, y = y, x % y

    return x


def get_planes(index, structure):
    # based on structure, return family of crystal planes
    planes = []
    index = list(index)
    h, k, l = float(index[0]), float(index[1]), float(index[2])
    if structure == 'BCC' or structure == 'FCC':
        for _ in range(2):
            h *= -1
            for _ in range(2):
                k *= -1
                for _ in range(2):
                    l *= -1
                    for item in permutations([h, k, l]):
                        planes.append(item)
    elif structure == 'HCP':
        H = (2 * h - k) / 3
        K = (2 * k - h) / 3
        I = -(H + K)
        L = l
        for _ in range(2):
            H *= -1
            for _ in range(2):
                K *= -1
                for _ in range(2):
                    I *= -1
                    for _ in range(2):
                        L *= -1
                        for item in permutations([H, K, I, L]):
                            h = int((item[0] - item[2]) * 3)
                            k = int((item[1] - item[2]) * 3)
                            l = int(item[3] * 3)
                            divisor = hcf(hcf(abs(h), abs(k)), abs(l))
                            h /= divisor
                            k /= divisor
                            l /= divisor
                            planes.append((h, k, l))
    # Remove duplicate entries
    planes = list(set(planes))
    return planes


def make_grid(*args):
    '''
    make grid of list of arguments
    suppose we have 4 arguments, each has [M, N, P, Q] entries
    the q arguments vary the fastest
    for an arbitrary permute [m, n, p, q], the index is
    q + pQ + nPQ + mNPQ = q+Q(p+P(n+mN))
    '''
    num_var = len(args)
    num_permut = int(reduce(lambda count, arg: count * len(arg), args, 1))
    result = np.zeros((num_permut, num_var))
    for i in range(num_permut):
        index = i
        for j in reversed(range(num_var)):
            sub_index = int(index % len(args[j]))
            result[i, j] = args[j][sub_index]
            index /= len(args[j])
    return result


def gen_fcc(dim, latt_param):
    '''
    generate fcc structure
    dim of length 3
    '''
    dim = [dim] * 3
    x_dim, y_dim, z_dim = dim
    x_rep, y_rep, z_rep = int(x_dim / latt_param), int(y_dim / latt_param), int(
        z_dim / latt_param)
    prim_block = np.array([[0., 0., 0.], [latt_param / 2, latt_param / 2, 0.0],
                           [latt_param / 2, 0.0, latt_param / 2],
                           [0.0, latt_param / 2, latt_param / 2]])
    reps = make_grid(range(x_rep), range(y_rep), range(z_rep))
    bulk_xyz = np.empty((reps.shape[0] * 4, 3), dtype=float)
    for i, rep in enumerate(reps):
        disp = rep * latt_param
        bulk_xyz[i * 4:i * 4 + 4, :] = prim_block + disp
    center = np.sum(bulk_xyz, axis=0) / bulk_xyz.shape[0]
    bulk_xyz -= center
    return bulk_xyz


def gen_bcc(dim, latt_param):
    '''
    generate bcc structure
    dim of length 3
    '''
    dim = [dim] * 3
    x_dim, y_dim, z_dim = dim
    x_rep, y_rep, z_rep = int(x_dim / latt_param), int(y_dim / latt_param), int(
        z_dim / latt_param)
    prim_block = np.array([[0., 0., 0.], [latt_param / 2, latt_param / 2,
                                          latt_param / 2]])
    reps = make_grid(range(x_rep), range(y_rep), range(z_rep))
    bulk_xyz = np.empty((reps.shape[0] * 2, 3), dtype=float)
    for i, rep in enumerate(reps):
        disp = rep * latt_param
        bulk_xyz[i * 2:i * 2 + 2, :] = prim_block + disp
    center = np.sum(bulk_xyz, axis=0) / bulk_xyz.shape[0]
    bulk_xyz -= center
    return bulk_xyz


def gen_hcp(dim, latt_param_a, latt_param_c):
    '''
    generate hcp structure
    dim of length 3
    '''
    dim = [dim] * 3
    x_dim, y_dim, z_dim = dim
    x_rep, y_rep, z_rep = int(x_dim / latt_param_a), int(y_dim / latt_param_a), int(
        z_dim / latt_param_c)
    prim_block = np.array(
        [[latt_param_a / 3.0, 2.0 * latt_param_a / 3.0, latt_param_c / 4.0],
         [2.0 * latt_param_a / 3.0, latt_param_a / 3.0, 3.0 * latt_param_c / 4.0]])
    reps = make_grid(range(x_rep), range(y_rep), range(z_rep))
    bulk_xyz = np.empty((reps.shape[0] * 2, 3), dtype=float)
    coord_transform = [[1.0, -0.5, 0.0], [0.0, np.sqrt(3) / 2.0, 0.0], [0.0, 0.0, 1.0]]
    for i, rep in enumerate(reps):
        dist = [latt_param_a * rep[0], latt_param_a * rep[1], latt_param_c * rep[2]]
        a1a2c = prim_block + dist
        xyz = np.mat(coord_transform) * np.mat(a1a2c).T
        bulk_xyz[i * 2:i * 2 + 2, :] = xyz.T
    center = np.sum(bulk_xyz, axis=0) / bulk_xyz.shape[0]
    bulk_xyz -= center
    return bulk_xyz


def gen_cluster(bulk_xyz, planes, length, d):
    planes = np.array(planes).T
    planes_norm = np.sqrt(np.sum(planes**2, axis=0))
    distance = np.dot(bulk_xyz, planes) / planes_norm
    under_plane_mask = np.sum(distance > length,
                              axis=1) == 0
    valid_atoms = np.arange(bulk_xyz.shape[0])[under_plane_mask]
    return distance, valid_atoms


def surf_count(coors, distance_threshold, strucutre):
    natoms = coors.shape[0]
    cn_mat = np.zeros((natoms, 13), dtype=int) # matrix of coordinate atoms
    coor_number = np.zeros(natoms, dtype=float)
    for i, icoor in enumerate(coors):
        dist_list = np.sqrt(np.sum((icoor - coors) ** 2, axis=1)) # list of distance
        coor_number[i] = np.sum(dist_list < distance_threshold) - 1 # list of coordinate number
        icn = np.arange(natoms)[dist_list < distance_threshold] # list of coordinate atoms
        idx = np.argwhere(icn == i) 
        icn = np.delete(icn, idx)  # delete the element which equal to i
        cn_mat[i][0] = icn.shape[0] 
        cn_mat[i, 1: 1 + icn.shape[0]] = icn
    accum_cn_mat = np.zeros(natoms, dtype=float)
    gcn = np.zeros(natoms, dtype=float)
    for i, line in enumerate(cn_mat):
        for j in range(1, line[0] + 1):
            accum_cn_mat[i] += cn_mat[cn_mat[i, j], 0]
        if strucutre == 'BCC':
            gcn[i] = accum_cn_mat[i]/8.0
            nsurf = np.sum(coor_number < 7)
            surfcn = float(np.sum(cn_mat[:, 0][cn_mat[:, 0] < 7])) / nsurf
        else:
            gcn[i] = accum_cn_mat[i]/12.0
            nsurf = np.sum(coor_number < 10)
            surfcn = float(np.sum(cn_mat[:, 0][cn_mat[:, 0] < 10])) / nsurf
    return (coor_number, gcn, nsurf, surfcn)


class Wulff:
    def __init__(self) -> None:
        self.ele = ''
        self.structure = ''
        self.latt_para_a = 0.0
        self.latt_para_c = 0.0
        self.A_atoms = np.array([])
        self.P = 0.0  # pressure
        self.T = 0.0  # temperature
        self.d = 0.0  # radius of nanoparticle

        self.nGas = 3
        self.rPP = np.array([])  # partial pressure
        self.S_gas = np.array([[]])  # factors to compute adsorption entropy (of each gas)
        self.ads_type = np.array([[]])  # adsorption type of each gas
        self.thetaML = np.array([])  # average surface coverage (obtained from MD)

        self.face_num = 0  # number of faces
        self.face_index = np.array([])  # miller index of each face
        self.gamma = np.array([])  # surface energy
        self.E_ads = np.array([[]])  # adosorption energy (of each gas on each face)
        self.S_ads = np.array([[]])  # adosorption entropy (of each gas on each face)
        self.w = np.array([[[]]])  # interaction energy between gases (on each face)

        self.coverage = np.array([])  # coverage of each face
        self.revised_gamma = np.array([])  # revised gamma of each face
        self.bond_length = 3.0

        self.positions = np.array([])
        self.eles = np.array([])
        self.nAtoms = 0
        self.siteTypes = np.array([])

    def get_para(self, paradic):
        gas_flag = [1, 1, 1]
        self.ele = paradic["Element"]
        self.structure = paradic["Crystal structure"]
        try:
            self.latt_para_a = float(paradic["Lattice constant"])
            self.P = float(paradic["Pressure"])
            self.T = float(paradic["Temperature"])
        except ValueError:
            pass
        
        paradic = paradic["MSR"]
        self.d = float(paradic["Radius"])
        # Gases Info
        self.nGas = 3
        PP_l = [paradic["Gas1_pp"], paradic["Gas2_pp"], paradic["Gas3_pp"]]
        S_l = [paradic["Gas1_S"], paradic["Gas2_S"], paradic["Gas3_S"]]
        type_l = [paradic["Gas1_type"], paradic["Gas2_type"], paradic["Gas3_type"]]
        for i in range(self.nGas):
            if not PP_l[i]:
                gas_flag[i] = 0
                self.nGas -= 1
            else:
                PP = float(PP_l[i])
                rPP = PP * self.P / 100.0
                self.rPP = np.append(self.rPP, rPP)
                S = float(S_l[i]) - k_b*np.log(rPP/P0)
                self.S_gas = np.append(self.S_gas, S)
                self.ads_type = np.append(self.ads_type, type_l[i])

        # Faces Info
        self.face_num = paradic["nFaces"]
        self.E_ads = np.zeros((self.face_num, self.nGas))
        self.S_ads = np.zeros((self.face_num, self.nGas))
        self.w = np.zeros((self.face_num, self.nGas, self.nGas))
        self.thetaML = np.ones((self.face_num))
        self.face_d = {}
        for m in range(self.face_num):
            facedic = paradic[f"Face{m+1}"]
            face = facedic["index"]
            self.face_index = np.append(self.face_index, face)
            index = [int(s) for s in re.findall(r"-*[0-9]", face)]
            if len(index) != 3:
                message = f"Please check the face index of face{m+1}"
                return False, message
            h, k, l = index[0], index[1], index[2]
            # calculate areas
            if self.structure == 'FCC':
                self.bond_length = 1.45/2*self.latt_para_a
                if h % 2 != 0 and k % 2 != 0 and l % 2 != 0:
                    A = self.latt_para_a**2 * np.sqrt(h**2 + k**2 + l**2) / 4.0
                    distance = self.latt_para_a**3 / A / 4.0
                else:
                    A = self.latt_para_a**2 * np.sqrt(h**2 + k**2 + l**2) / 2.0
                    distance = self.latt_para_a**3 / A / 2.0
            elif self.structure == 'BCC':
                self.bond_length = 1.75/2*self.latt_para_a
                if (h + k + l) % 2 != 0:
                    A = self.latt_para_a**2 * np.sqrt(h**2 + k**2 + l**2)
                    distance = self.latt_para_a**3 / A
                else:
                    A = self.latt_para_a**2 * np.sqrt(h**2 + k**2 + l**2) / 2.0
                    distance = self.latt_para_a**3 / A / 2.0
            elif self.structure == 'HCP':
                self.bond_length = 1.05*self.latt_para_a
                if (2 * h + k) % 3 == 0 and l % 2 != 0:
                    A = np.sqrt(3.0) * self.latt_para_a**2 * self.latt_para_c * np.sqrt(
                        0.75 * (h**2 + h * k + k**2) / (self.latt_para_a**2) +
                        (l / self.latt_para_c)**2) / 4.0
                    distance = self.latt_para_a**2 * self.latt_para_c / A / 4.0
                else:
                    A = np.sqrt(3.0) * self.latt_para_a**2 * self.latt_para_c * np.sqrt(
                        0.75 * (h**2 + h * k + k**2) / (self.latt_para_a**2) +
                        (l / self.latt_para_c)**2) / 2.0
                    distance = self.latt_para_a**2 * self.latt_para_c / A / 2.0
            self.face_d[face] = distance
            self.A_atoms = np.append(self.A_atoms, A)
            self.gamma = np.append(self.gamma, float(facedic["gamma"]))
            E_ads_buff = np.array(facedic["E_ads"])
            S_ads_buff = np.array(facedic["S_ads"])
            w_list = np.array(facedic["w"])
            x = 0
            for i, flag in enumerate(gas_flag):
                if flag == 1:
                    self.E_ads[m, x] = E_ads_buff[i]
                    self.S_ads[m, x] = S_ads_buff[i]
                    y = 0
                    for j, inner_flag in enumerate(gas_flag):
                        if inner_flag == 1:
                            self.w[m, x, y] = w_list[i][j]
                            y += 1
                    x += 1
        return True, ""

    def gen_coverage(self):
        # generate coverage based on
        self.coverage = np.zeros((self.face_num, self.nGas))
        for m in range(self.face_num):
            # solve coverage
            theta = np.array([])

            def func(TTT):
                TT = np.zeros((self.nGas))
                f = np.zeros((self.nGas + 1))
                for k in range(self.nGas):
                    TT[k] = TTT[k]
                # calculate w
                cal_w = np.mat(self.w[m]) * np.mat(TT).T
                cal_w = cal_w.getA().flatten()
                for k in range(self.nGas):
                    if (self.ads_type[k] == "Associative"):
                        f[k] = TTT[k] * np.exp(
                            (self.E_ads[m, k] - cal_w[k] - self.T * (self.S_ads[m, k] - self.S_gas[k])) /
                            (k_b * self.T)) / self.rPP[k] - TTT[-1]
                    elif (self.ads_type[k] == "Dissociative"):
                        f[k] = TTT[k] * (np.exp(
                            (2 * self.E_ads[m, k] - 2 * cal_w[k] - self.T * (self.S_ads[m, k] - self.S_gas[k]))
                            / (k_b * self.T)) / self.rPP[k])**0.5 - TTT[-1]
                f[-1] = np.sum(TTT) - 1
                return f

            # iteration and check solution
            while True:
                theta = fsolve(func, np.random.rand(self.nGas + 1))
                if (theta > 0).all() and abs(np.sum(func(theta))) < 10**(-6):
                    break
            # finding indices where theta >= self.thetaML[m]
            for j in range(self.nGas):
                if theta[j] >= self.thetaML[m]:
                    theta = np.zeros((self.nGas))
                    theta[j] = self.thetaML[m]
            for k in range(self.nGas):
                self.coverage[m][k] = theta[k]

    def gen_surface_energies(self):
        planes, surface_energies = [], []
        self.revised_gamma = np.zeros((self.face_num))
        self.planes_dict = {}

        for m in range(self.face_num):
            r_gamma = 0.0
            r_ads = np.zeros((self.nGas))
            cal_w = np.mat(self.w[m]) * np.mat(self.coverage[m]).T
            cal_w = cal_w.getA().flatten()
            r_ads = (self.E_ads[m] - cal_w) / self.A_atoms[m]
            r_gamma = np.mat(self.coverage[m]) * np.mat(r_ads).T
            self.revised_gamma[m] = float(self.gamma[m] + r_gamma)

            plane = get_planes(self.face_index[m], self.structure)
            for p in plane:
                self.planes_dict[p] = self.face_index[m]
            planes += plane
            surface_energies += [self.revised_gamma[m]] * len(plane)
        return (planes, surface_energies)

    def mark_atoms(self, cn, valid_atoms, planes, distance):
        distance = distance[valid_atoms, :]
        max_d = np.max(distance, axis=0)
        surf_type = np.array([])
        color_ele = np.array([])
        n_surfs = np.zeros(self.face_num)
        ratio_edges = np.zeros(self.face_num)
        ratio_corners = np.zeros(self.face_num)
        edge_corner_list = np.array([], dtype=int)
        nedges = 0
        ncorners = 0
        for n in range(len(valid_atoms)):
            count = 0
            surf_type = np.append(surf_type, '')
            color_ele = np.append(color_ele, 'O')
            if (self.structure=='FCC' and cn[n]<10) or (self.structure=='BCC' and cn[n]<7):
                for m, plane in enumerate(planes):
                    face = self.planes_dict[plane]
                    if distance[n, m] >= max_d[m] - 0.45*self.face_d[face]:
                        p = face
                        surf_type[n] += f"{p} "
                        count += 1
                if count == 1:
                    n_surfs[np.argwhere(self.face_index==p)] += 1
                    if p == '100':
                        color_ele[n] = 'Au'
                    elif p == '110':
                        color_ele[n] = 'Cu'
                    elif p == '111':
                        color_ele[n] = 'Fe'
                    else:
                        color_ele[n] = 'Rh'
                elif count >= 2:
                    edge_corner_list = np.append(edge_corner_list, n)
                else:
                    surf_type[n] = 'subsurface'   
            else:
                surf_type[n] = ' bulk'
                color_ele[n] = 'Co'
        for n in edge_corner_list:
            surf_type_a = np.array(surf_type[n].split(), dtype=str)
            for m, face_id in enumerate(self.face_index):
                if n_surfs[m] == 0:
                    surf_type_a = surf_type_a[surf_type_a != face_id]
            l = len(surf_type_a)
            if l == 1:
                p = surf_type_a[0]
                n_surfs[np.argwhere(self.face_index==p)] += 1
                if p == '100':
                    color_ele[n] = 'Au'
                elif p == '110':
                    color_ele[n] = 'Cu'
                elif p == '111':
                    color_ele[n] = 'Fe'
                else:
                    color_ele[n] = 'Rh'
            elif l == 2:
                surf_type[n] = 'edge'
                nedges += 1
                ratio_edges[np.argwhere(self.face_index==surf_type_a[0])] += 0.5
                ratio_edges[np.argwhere(self.face_index==surf_type_a[1])] += 0.5
                color_ele[n] = 'Pt'
            elif l >= 3:
                surf_type[n] = 'corner'
                ncorners += 1
                r = 1.0/l
                for face in surf_type_a:
                    ratio_corners[np.argwhere(self.face_index==face)] += r
                color_ele[n] = 'Pd'
            else: 
                surf_type[n] = 'unkonwn'
        return (surf_type, color_ele, n_surfs, ratio_edges, ratio_corners, ncorners, nedges)

    def geometry(self):
        planes, surface_energies = self.gen_surface_energies()
        if sum(self.revised_gamma > 0) != self.face_num:
            message = "Nanoparticle broken \n\nNegative surface energy "
            return 0, message
        length = [e * self.d / np.min(surface_energies) for e in surface_energies]
        length = np.array(length)
        bulk_dim = np.min(length) * 3
        if self.structure == 'FCC':
            bulk = gen_fcc(bulk_dim, self.latt_para_a)
        elif self.structure == 'BCC':
            bulk = gen_bcc(bulk_dim, self.latt_para_a)
        elif self.structure == 'HCP':
            bulk = gen_hcp(bulk_dim, self.latt_para_a, self.latt_para_c)
        distance, valid_atoms = gen_cluster(bulk, planes, length, self.d)
        coor_valid = bulk[valid_atoms]
        N_atom = coor_valid.shape[0]
        cn, gcn, nsurf, surfcn = surf_count(coor_valid, self.bond_length, self.structure)
        self.positions = np.array(coor_valid)
        self.nAtoms = np.array(N_atom)
        self.eles = [self.ele for i in range(self.nAtoms)]
        surf_type, color_ele, n_surfs, ratio_edges, ratio_corners, ncorners, nedges = self.mark_atoms(cn, valid_atoms, planes, distance)
        self.siteTypes = np.array(surf_type)
        filename_xyz = f"data/OUTPUT/{self.ele}_{self.structure}_T_{self.T}_P_{self.P}_cluster.xyz"
        with open(filename_xyz, 'w') as fp_xyz:
            with open('data/INPUT/ini.xyz', 'w') as kmc_ini:
                fp_xyz.write('%d\n' % (N_atom))
                fp_xyz.write('cluster_%d_%d.xyz\n' % (self.T, self.P))
                kmc_ini.write('%d\n\n' % (N_atom))
                for i in range(N_atom):
                    fp_xyz.write('%s  %.3f  %.3f  %.3f  %s\n' %
                                 (color_ele[i], coor_valid[i][0], coor_valid[i][1],
                                  coor_valid[i][2], surf_type[i]))
                    kmc_ini.write('%s  %.3f  %.3f  %.3f\n' %
                                  (self.eles[i], coor_valid[i][0], coor_valid[i][1],
                                   coor_valid[i][2]))
        record_df = pd.DataFrame(columns=self.face_index)
        record_df.loc['number'] = n_surfs
        # record_df.loc['n_edges'] = ratio_edges
        # record_df.loc['n_corners'] = ratio_corners
        # record_df.loc['Atom area'] = self.A_atoms
        # record_df.loc['Surface tension'] = self.revised_gamma
        for i in range(self.nGas):
            record_df.loc[f'coverage{i+1}'] = self.coverage[:,i]
        record_df = record_df.applymap(lambda x: '%.2f'%x)
        # record_df.loc['n_edges'] = pd.to_numeric(record_df.loc['n_edges'])
        # record_df.loc['n_corners'] = pd.to_numeric(record_df.loc['n_corners'])
        record_df['edges'] = '/'
        record_df['corners'] = '/'
        record_df['subsurface'] = '/'
        record_df.loc['number', 'edges'] = nedges
        record_df.loc['number', 'corners'] = ncorners
        record_df.loc['number', 'subsurface'] = nsurf-n_surfs.sum()-nedges-ncorners
        record_df.loc['number'] = record_df.loc['number'].astype(float).astype(int)
        self.record_df = record_df
        with open('data/OUTPUT/faceinfo.txt', 'w') as fo:
            fo.write(record_df.__repr__())
        # return (self.face_index, self.coverage, self.gamma, self.revised_gamma)
        return 1, ""


if __name__ == '__main__':
    warnings.showwarning = handle_warning
