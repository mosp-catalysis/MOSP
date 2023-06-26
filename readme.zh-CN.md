Language : [🇺🇸](./README.md) | 🇨🇳

# MOSP: Multi-scale Operando Simulation Package

> **Note**  
> 已知bug：重复运行kmc后程序有概率崩溃，需要关闭主窗口重新运行。该问题将在下个版本中修复  

## 关于MOSP  

MOSP是一个多尺度的原位模拟模拟包, 用户可以通过GUI界面便捷输入反应条件和纳米颗粒大小等参数，在数秒内获得真实环境下的NPs结构，并通过动力学蒙特卡洛方法(kmc)在宏观时间尺度上模拟纳米颗粒在该反应环境下的催化行为。  
MOSP由[高嶷团队](https://www.x-mol.com/groups/gao_yi)开发和维护, 欢迎与我们进行交流和讨论。  

MOSP is contributed by [Yi Gao's group](https://www.x-mol.com/groups/gao_yi). The major contributors: Beien Zhu, Lei Ying, Yu Han, Xiaoyan Li, Jun Meng, Yi Gao. 

## 安装

1. 安装python (建议使用python3.8版本)  
  从[python官网](https://www.python.org/downloads/release/python-3816/)获取3.8版本python，或安装[Anaconda](https://www.anaconda.com/download)

2. 下载项目  
   - 方法1：通过git拷贝到本地  
        从[git官网](https://git-scm.com/downloads)下载并安装git后，可以通过Git Bash将MOSP拷贝到本地, 命令如下
        ```python
        # 方案1：从GitHub下载项目
        git clone https://github.com/mosp-catalysis/MOSP.git  
        # 方案2：从Gitee下载项目
        git clone https://gitee.com/mosp-catalysis/MOSP.git
        # 进入主目录
        cd MOSP  
        ```  
   - 方法2：下载[压缩包](https://github.com/mosp-catalysis/MOSP/archive/refs/heads/main.zip)，解压后进入MOSP-main目录  
  
3. 安装依赖 (如果您使用的是32操作系统或其他版本的python，请在[这里](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyopengl)下载对应版本PyOpenGl的.whl文件)  
    ```python
    # (可选)创建anaconda环境
    conda create -n mosp_env python=3.8
    conda activate mosp_env
    # 安装依赖
    pip install PyOpenGL-3.1.6-cp38-cp38-win_amd64.whl  
    pip install PyOpenGL_accelerate-3.1.6-cp38-cp38-win_amd64.whl  
    pip install -r requirements.txt  
    ```
4. 运行  
    ```python
    # (可选)激活anaconda环境
    conda activate mosp_env
    # 运行主程序
    python main.py
    ```

## 使用  

![gui_window](docs/demo.gif "gui_window")  
- input/文件夹内提供了Au和Pt的示例输入文件，后续版本将陆续补充更多示例

## 版本
- v1.0: 基础功能，msr与kmc模块接入

## References  

### **MSR**

[1] Zhu B, Xu Z, Wang CL, Gao Y,* "Shape Evolution of Metal Nanoparticles in Water Vapor Environments." *Nano Lett.* **2016**, *16*, 2628-2632. [<a href="https://pubs.acs.org/doi/abs/10.1021/acs.nanolett.6b00254">Link</a>]

[2] Zhu B, Meng J, Yuan W, Zhang X, Yang H, Wang Y,* Gao Y,* "Reshaping of Metal Nanoparticles in Reaction Conditions." *Angew. Chem. Int. Ed.* **2020**, *59*, 2171-2180. (minireview) [<a href="https://onlinelibrary.wiley.com/doi/abs/10.1002/anie.201906799#:~:text=The%20shape%20of%20metal%20nanoparticles%20%28NPs%29%20is%20one,fully%20understanding%20catalytic%20mechanisms%20at%20the%20molecular%20level.">Link</a>]


### **KMC**  

[1] Li X, Zhu B,* Gao Y,* "Exploration of Dynamic Structure–Activity Relationship of a Platinum Nanoparticle in the CO Oxidation Reaction" *J. Phys. Chem. C* **2021**, *125*, 19756-19762. [<a href="https://pubs.acs.org/doi/10.1021/acs.jpcc.1c05339">Link</a>]

## Related Publications  

[1] Zhu B, Meng J, Gao Y,* "Equilibrium Shape of Metal Nanoparticles under Reactive Gas Conditions." *J. Phys. Chem. C* **2017**, *121*, 5629-5634. [<a href="https://pubs.acs.org/doi/10.1021/acs.jpcc.6b13021">Link</a>]

[2] Zhang X, Meng J, Zhu B,* Yu J, Zou S, Zhang Z, Gao Y,* Wang Y,* "In situ TEM Studies of Shape Evolution of Pd Nanoparticles under Oxygen and Hydrogen Environment at Atmospheric Pressure." *Chem. Comm.* **2017**, *53*, 13213-13216. (back cover) [<a href="https://pubs.rsc.org/en/content/articlelanding/2017/cc/c7cc07649e">Link</a>]

[3] Meng J, Zhu B,* Gao Y,* "Shape Evolution of Metal Nanoparticles in Binary Gas Environment." *J. Phys. Chem. C* **2018**, *122*, 6144-6150. [<a href="https://pubs.acs.org/doi/10.1021/acs.jpcc.8b00052">Link</a>]

[4] Duan M, Yu J, Meng J, Zhu B,* Wang Y,* Gao Y,* "Reconstruction of Supported Metal Nanoparticles in Reaction Conditions." *Angew. Chem. Int. Ed.* **2018**, *57*, 6464-6469. (minireview) [<a href="https://www.onlinelibrary.wiley.com/doi/abs/10.1002/anie.201800925">Link</a>]

[5] Zhang X, Meng J, Zhu B,* Yuan W, Yang H, Zhang Z, Gao Y,* Wang Y,* "Unexpected N<sub>2</sub> Induced Refacetting of Palladium Nanoparticles." *Chem. Comm.* **2018**, *54*, 8587-8590. [<a href="https://pubs.rsc.org/en/content/articlelanding/2018/cc/c8cc04574g">Link</a>]

[6] Chmielewski A, Meng J, Zhu B, Gao Y, Guesmi H, Prunier H, Alloyeau D, Wang G, Louis C, Dalannoy L, Afanasiev P, Ricolleau C, Nelayah J,* "Reshaping Dynamics of Gold Nanoparticles under H<sub>2</sub> and O<sub>2</sub> at Atmospheric Pressure." *ACS Nano* **2019**, *13*, 2024-2033. [<a href="https://pubs.acs.org/doi/abs/10.1021/acsnano.8b08530?src=recsys">Link</a>]

[7] Du J, Meng J, Li X, Zhu B, Gao Y,* "Multiscale Atomistic Simulation of Metal Nanoparticles in Working Conditions." *Nanoscale Adv.* **2019**, *1*, 2478-2484. [<a href="https://pubs.rsc.org/en/content/articlepdf/2019/na/c9na00196d?page=search#:~:text=Multiscale%20atomistic%20simulation%20of%20metal%20nanoparticles%20under%20working,conditions%20have%20been%20discovered%20in%20recent%20years%2C%20which">PDF</a>]

[8] Yuan L, Zhu B, Zhang G,* Gao Y,* "Reshaping of Rh Nanoparticles in Operando Conditions." *Catal. Today* **2020**, *350*, 184-191. [<a href="https://www.sciencedirect.com/science/article/abs/pii/S0920586119303141">Link</a>]

[9] Tang M, Zhu B, Meng J, Zhang X, Yuan W, Zhang Z, Gao Y,* Wang Y,* "Pd-Pt Nanoalloy Transformation Pathways at Atomic Scale." *Mater. Today Nano* **2018**, *1*, 41-46. [<a href="https://www.sciencedirect.com/science/article/pii/S2588842018300324">Link</a>]

[10] Li X, Zhu B, Qi R, Gao Y,* "Real-time Simulation of Nonequilibrium Nanocrystal Transformation." *Adv. Theory Simul.* **2019**, *2*, 1800127.[<a href="https://onlinelibrary.wiley.com/doi/abs/10.1002/adts.201800127">Link</a>]

[11] Wu Z, Tang M, Li X, Luo S, Yuan W, Zhu B,* Zhang H, Gao Y, Wang Y,* "Surface faceting and compositional evolution of Pd@Au core−shell nanocrystals during in situ annealing." *Phys. Chem. Chem. Phys.* **2019**, *21*, 3134-3139. [<a href="https://pubs.rsc.org/en/content/articlelanding/2019/cp/c8cp07576j">Link</a>]

[12] Zhu B, Qi R, Yuan L, Gao Y,* "Real-time Simulation of the Atomic Ostwald Ripening of TiO<sub>2</sub> Supported Nanoparticles." *Nanoscale* **2020**, *12*, 19142-19148. [<a href="https://pubs.rsc.org/en/content/articlelanding/2020/nr/d0nr04571c">Link</a>]

[13] Duan X, Li X, Zhu B,* Gao Y,* "Identifying the morphology of Pt nanoparticles for the optimal catalytic activity towards CO oxidation." *Nanoscale* **2022**, *14*, 17754-17760. [<a href="https://pubs.rsc.org/en/content/articlelanding/2022/NR/D2NR04929E">Link</a>]


