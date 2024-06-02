import numpy as np
import json

def str2zero(inp):
    if type(inp) == str:
        inp = 0
    return inp

def writeKmcInp(values):
    try:
        if values['Crystal structure'] == 'FCC':
            bond_length = 1.45/2*float(values['Lattice constant'])
        elif values['Crystal structure'] == 'BCC':
            bond_length = 1.75/2*float(values['Lattice constant'])
        bond_length = (int(bond_length*10) + 1)/10.0

        kmc_values = values['KMC']
        with open('data/INPUT/input.txt', 'w') as f_ini:
            f_ini.write(f"{values['Temperature']}\t\t ! Temperature (K)\n")
            f_ini.write(f"{values['Pressure']}\t\t ! Pressure (Pa)\n")
            f_ini.write(f"{bond_length}\t\t ! Bond length (A)\n")
            f_ini.write(f"{kmc_values['nspecies']}\t\t ! Num of species\n")
            f_ini.write(f"{kmc_values['nevents']}\t\t ! Num of events\n")
            f_ini.write(f"{kmc_values['nproducts']}\t\t ! Num of products\n")
            f_ini.write(f"{kmc_values['nLoop']}\t\t ! Num of steps\n")
            f_ini.write(f"{kmc_values['record_int']}\t\t ! record inteval\n")

        li = np.array(kmc_values["li"])
        li = li.astype(np.float32)
        np.savetxt("data/INPUT/li.txt", li, fmt="%.3f", delimiter="\t")

        with open('data/INPUT/species.txt', 'w') as s_ini:
            for n in range(kmc_values['nspecies']): 
                # note that ID is starting from 1
                spe_dict = json.loads(kmc_values[f"s{n+1}"])
                s_ini.write(f"ID: {n+1}\n")
                s_ini.write(f"Name: {spe_dict['name']}\n")
                s_ini.write(f"is_twosite: {spe_dict['is_twosite']}\n")
                s_ini.write(f"mass: {spe_dict['mass']}\n")
                s_ini.write(f"S_gas0: {spe_dict['S_gas']}\n")
                s_ini.write(f"S_ads: {spe_dict['S_ads']}\n")
                s_ini.write(f"sticking: {spe_dict['sticking'][0]} {spe_dict['sticking'][1]}\n")
                s_ini.write(f"E_ads_para: {spe_dict['E_ads_para'][0]} {spe_dict['E_ads_para'][1]} {spe_dict['E_ads_para'][2]}\n")
                s_ini.write(f"Ea_diff: {spe_dict['Ea_diff']}\n")
                s_ini.write(f"PP_ratio: {float(spe_dict['PP_ratio'])*0.01}\n")
                s_ini.write(f"\n")

        with open('data/INPUT/products.txt', 'w') as p_ini:
            for n in range(kmc_values['nproducts']):
                # again: note that ID is starting from 1
                pro_dict = json.loads(kmc_values[f"p{n+1}"])
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
                    "Diffusion": "diff", "Reaction": "rec"}
        with open('data/INPUT/events.txt', 'w') as e_ini:
            for n in range(kmc_values['nevents']): 
                # again: note that ID is starting from 1
                evt_dict = json.loads(kmc_values[f"e{n+1}"])
                e_ini.write(f"ID: {n+1}\n")
                e_ini.write(f"Name: {evt_dict['name']}\n")
                e_ini.write(f"event_type: {type_alias[evt_dict['type']]}\n")
                e_ini.write(f"is_twosite: {evt_dict['is_twosite']}\n")
                e_ini.write("cov_before: " 
                            + f"{str2zero(evt_dict['cov_before'][0])} "
                            + f"{str2zero(evt_dict['cov_before'][1])}\n")
                e_ini.write("cov_after: " 
                            + f"{str2zero(evt_dict['cov_after'][0])} "
                            + f"{str2zero(evt_dict['cov_after'][1])}\n")
                if evt_dict['type'] == 'Reaction':
                    e_ini.write(f"BEP_para: {evt_dict['BEP_para'][0]} "
                                + f"{evt_dict['BEP_para'][1]}\n")
                e_ini.write("\n")
        return True
    except:
        return False