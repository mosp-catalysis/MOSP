# -*- coding: utf-8 -*-
from tkinter.messagebox import askyesno, showerror
from scipy.optimize import fsolve
from functools import reduce
from itertools import permutations
import warnings
import numpy as np

R = 8.314
unit_coversion = 0.0000103643
k_b = 0.000086173303
bond_length = 3.0


# pause if warning
def handle_warning(message, category, filename, lineno, file=None, line=None):
    q = 'A warning occurred:\n"' + str(message) + '"\nDo you wish to continue?'
    response = askyesno(title='Warnings', message=q)

    if not response:
        raise category(message)


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
    under_plane_mask = np.sum(np.dot(bulk_xyz, planes) / planes_norm > length,
                              axis=1) == 0
    valid_atoms = np.arange(bulk_xyz.shape[0])[under_plane_mask]
    return bulk_xyz[valid_atoms]


def surf_count(coors, distance_threshold):
    # count the low-index surface (111), (100), (110) atom numbers
    # input coors is numpy array of shape (natoms, 3)
    # return (#atoms of 111, #atoms of 100, #atoms of 110)
    # 111 surface the sum of CN of neighbouring atoms is 90
    # 100 surface the sum of CN of neighbouring atoms is 80
    # 110 surface the sum of CN of neighbouring atoms is 70
    natoms = coors.shape[0]
    cn_mat = np.zeros((natoms, 13), dtype=int)  # matrix of coordinate atoms
    coor_number = np.zeros(natoms, dtype=float)
    for i, icoor in enumerate(coors):
        dist_list = np.sqrt(np.sum((icoor - coors)**2, axis=1))  # list of distance
        coor_number[i] = np.sum(
            dist_list < distance_threshold) - 1  # list of coordinate number
        icn = np.arange(natoms)[dist_list <
                                distance_threshold]  # list of coordinate atoms
        idx = np.argwhere(icn == i)
        icn = np.delete(icn, idx)  # delete the element which equal to i
        cn_mat[i][0] = icn.shape[0]
        cn_mat[i, 1:1 + icn.shape[0]] = icn
    accum_cn_mat = np.zeros(natoms, dtype=float)
    for i, line in enumerate(cn_mat):
        for j in range(1, line[0] + 1):
            accum_cn_mat[i] += cn_mat[cn_mat[i, j], 0]

    n100 = np.sum(coor_number == 8)
    n111 = np.sum(coor_number == 9)
    nsurf = np.sum(coor_number < 10)
    n110 = 0
    e110111 = 0
    e100111 = 0
    e100110 = 0
    conner = 0
    for i, tn in enumerate(coor_number):
        if tn == 7:
            if accum_cn_mat[i] >= 68:
                n110 += 1
            elif accum_cn_mat[i] >= 65:
                e110111 += 1
            else:
                e100111 += 1
        elif tn == 6:
            if accum_cn_mat[i] >= 56:
                e100110 += 1
            else:
                conner += 1
    nedge = nsurf - n100 - n110 - n111
    ntotal = natoms
    surfcn = float(np.sum(cn_mat[:, 0][cn_mat[:, 0] < 10])) / nsurf

    return (n100, n110, n111, e100110, e100111, e110111, conner, nedge, nsurf, ntotal,
            surfcn)


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

    def get_para(self, paradic):
        gas_flag = [1, 1, 1]
        self.ele = paradic["Element"]
        self.structure = paradic["Crystal structure"]
        try:
            self.latt_para_a = float(paradic["Lattice constant"])
            self.P = float(paradic["Pressure"])
            self.T = float(paradic["Temperature"])
            self.d = float(paradic["Radius"])
        except ValueError:
            pass

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
                self.S_gas = np.append(self.S_gas, float(S_l[i]))
                self.ads_type = np.append(self.ads_type, type_l[i])

        # Faces Info
        self.face_num = paradic["num_faces"]
        self.E_ads = np.zeros((self.face_num, self.nGas))
        self.S_ads = np.zeros((self.face_num, self.nGas))
        self.w = np.zeros((self.face_num, self.nGas, self.nGas))
        self.thetaML = np.ones((self.face_num))
        for m in range(self.face_num):
            facedic = paradic[m]
            face = facedic[f"{m}_index"]
            self.face_index = np.append(self.face_index, face)
            index = list(face)
            h, k, l = float(index[0]), float(index[1]), float(index[2])
            # calculate areas
            if self.structure == 'FCC':
                if h / 2 != 0 and k / 2 != 0 and l / 2 != 0:
                    A = self.latt_para_a**2 * np.sqrt(h**2 + k**2 + l**2) / 4.0
                else:
                    A = self.latt_para_a**2 * np.sqrt(h**2 + k**2 + l**2) / 2.0
            elif self.structure == 'BCC':
                if (h + k + l) / 2 != 0:
                    A = self.latt_para_a**2 * np.sqrt(h**2 + k**2 + l**2)
                else:
                    A = self.latt_para_a**2 * np.sqrt(h**2 + k**2 + l**2) / 2.0
            elif self.structure == 'HCP':
                if (2 * h + k) / 3 == 0 and l / 2 != 0:
                    A = np.sqrt(3.0) * self.latt_para_a**2 * self.latt_para_c * np.sqrt(
                        0.75 * (h**2 + h * k + k**2) / (self.latt_para_a**2) +
                        (l / self.latt_para_c)**2) / 4.0
                else:
                    A = np.sqrt(3.0) * self.latt_para_a**2 * self.latt_para_c * np.sqrt(
                        0.75 * (h**2 + h * k + k**2) / (self.latt_para_a**2) +
                        (l / self.latt_para_c)**2) / 2.0
            self.A_atoms = np.append(self.A_atoms, A)
            self.gamma = np.append(self.gamma, float(facedic[f"{m}_gamma"]))
            E_ads_buff = np.array([
                facedic[f"{m}_E_ads_Gas1"], facedic[f"{m}_E_ads_Gas2"],
                facedic[f"{m}_E_ads_Gas3"]
            ])
            S_ads_buff = np.array([
                facedic[f"{m}_S_ads_Gas1"], facedic[f"{m}_S_ads_Gas2"],
                facedic[f"{m}_S_ads_Gas3"]
            ])
            w_list = [[f"{m}_w_Gas1-Gas1", f"{m}_w_Gas1-Gas2", f"{m}_w_Gas1-Gas3"],
                      [f"{m}_w_Gas1-Gas2", f"{m}_w_Gas2-Gas2", f"{m}_w_Gas2-Gas3"],
                      [f"{m}_w_Gas1-Gas3", f"{m}_w_Gas2-Gas3", f"{m}_w_Gas3-Gas3"]]
            x = 0
            for i, flag in enumerate(gas_flag):
                if flag == 1:
                    self.E_ads[m, x] = E_ads_buff[i]
                    self.S_ads[m, x] = S_ads_buff[i]
                    y = 0
                    for j, inner_flag in enumerate(gas_flag):
                        if inner_flag == 1:
                            self.w[m, x, y] = facedic[w_list[i][j]]
                            y += 1
                    x += 1

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
                            (self.E_ads[m, k] - cal_w[k] + self.T * self.S_gas[k]) /
                            (k_b * self.T)) / self.rPP[k] - TTT[-1]
                    elif (self.ads_type[k] == "Dissociative"):
                        f[k] = TTT[k] * (np.exp(
                            (2 * self.E_ads[m, k] - 2 * cal_w[k] + self.T * self.S_gas[k])
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

        for m in range(self.face_num):
            r_gamma = 0.0
            r_ads = np.zeros((self.nGas))
            cal_w = np.mat(self.w[m]) * np.mat(self.coverage[m]).T
            cal_w = cal_w.getA().flatten()
            r_ads = (self.E_ads[m] - cal_w) / self.A_atoms[m]
            r_gamma = np.mat(self.coverage[m]) * np.mat(r_ads).T
            self.revised_gamma[m] = float(self.gamma[m] + r_gamma)

            plane = get_planes(self.face_index[m], self.structure)
            planes += plane
            surface_energies += [self.revised_gamma[m]] * len(plane)
        return (planes, surface_energies)

    def geometry(self):
        planes, surface_energies = self.gen_surface_energies()
        if sum(self.revised_gamma > 0) != self.face_num:
            showerror('   Unsuitable Condition Entered',
                      "Nanoparticle broken \n\nNegative surface energy ")
            return 0
        length = [e * self.d / np.min(surface_energies) for e in surface_energies]
        length = np.array(length)
        bulk_dim = np.min(length) * 3
        if self.structure == 'FCC':
            bulk = gen_fcc(bulk_dim, self.latt_para_a)
        elif self.structure == 'BCC':
            bulk = gen_bcc(bulk_dim, self.latt_para_a)
        elif self.structure == 'HCP':
            bulk = gen_hcp(bulk_dim, self.latt_para_a, self.latt_para_c)
        coor_valid = gen_cluster(bulk, planes, length, self.d)
        N_atom = coor_valid.shape[0]

        filename_xyz = f"{self.ele}_{self.structure}_T_{self.T}_P_{self.P}_cluster.xyz"
        with open(filename_xyz, 'w') as fp_xyz:
            with open('ini.xyz', 'w') as kmc_ini:
                fp_xyz.write('%d\n' % (N_atom))
                fp_xyz.write('cluster_%d_%d.xyz\n' % (self.T, self.P))
                kmc_ini.write('%d\n\n' % (N_atom))
                elements = [self.ele] * N_atom
                for i in range(N_atom):
                    fp_xyz.write('%s  %.3f  %.3f  %.3f\n' %
                                 (elements[i], coor_valid[i][0], coor_valid[i][1],
                                  coor_valid[i][2]))
                    kmc_ini.write('%s  %.3f  %.3f  %.3f\n' %
                                  (elements[i], coor_valid[i][0], coor_valid[i][1],
                                   coor_valid[i][2]))
        # return (self.face_index, self.coverage, self.gamma, self.revised_gamma)
        return 1


if __name__ == '__main__':
    warnings.showwarning = handle_warning
