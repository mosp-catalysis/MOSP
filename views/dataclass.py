# -*- coding: utf-8 -*-
"""
@author: yinglei
"""

from dataclasses import dataclass, field
from json import JSONEncoder, JSONDecoder


@dataclass
class Specie:
    default_name: str
    name: str = ""
    mass: float = 0.0
    PP_ratio: float = 0.0
    S_gas: float = 0.0
    Ea_diff: float = 0.0
    sticking: list = field(default_factory=list)
    E_ads_para: list = field(default_factory=list)

    is_twosite: bool = False
    flag_ads: bool = False
    flag_des: bool = False
    flag_diff: bool = False

    def __post_init__(self):
        if not self.sticking:
            self.sticking = [1.0, 1.0]
        if not self.E_ads_para:
            self.E_ads_para = [0.0, 0.0, 0.0]

    class Encoder(JSONEncoder):
        def default(self, o):
            return o.__dict__
        
    class Decoder(JSONDecoder):
        def decode(self, s):
            json_obj = super().decode(s)
            return Specie(**json_obj)


@dataclass
class Product:
    default_name: str
    name: str = ""
    num_gen: int = 0
    event_gen: list = field(default_factory=list)
    num_consum: int = 0
    event_consum: list = field(default_factory=list)
    
    class Encoder(JSONEncoder):
        def default(self, o):
            return o.__dict__
        
    class Decoder(JSONDecoder):
        def decode(self, s):
            json_obj = super().decode(s)
            return Product(**json_obj)


@dataclass
class Event:
    default_name: str
    name: str = ""
    type: str = ""
    is_twosite: bool = True
    cov_before: list = field(default_factory=list)
    cov_after: list = field(default_factory=list)
    BEP_para: list = field(default_factory=list)

    def __post_init__(self):
        if not self.cov_before:
            self.cov_before = [0, 0]
        if not self.cov_after:
            self.cov_after = [0, 0]
        if not self.BEP_para:
            self.BEP_para = [0.0, 0.0]

    class Encoder(JSONEncoder):
        def default(self, o):
            return o.__dict__
        
    class Decoder(JSONDecoder):
        def decode(self, s):
            json_obj = super().decode(s)
            return Event(**json_obj)

