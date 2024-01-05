import math

import requests
from pyscript import document

from .abstract_module import AbstractCalculationModule

class CalculationModule(AbstractCalculationModule):
    _in_memory: dict = {}

    def __init__(self, prefix_url: str, dom_elements: dict[str], load_datas: dict[str]) -> None:
        # init
        self._valid = False

        self.prefix_url = prefix_url
        self.dom_elements = dom_elements
        self.load_datas = load_datas

        self._point: dict = {
            "base_lv": int(dom_elements["base_lv"].value),
            "job_lv": int(dom_elements["base_lv"].value),
            "str": int(dom_elements["str"]["base"].value),
            "agi": int(dom_elements["agi"]["base"].value),
            "vit": int(dom_elements["vit"]["base"].value),
            "int": int(dom_elements["int"]["base"].value),
            "dex": int(dom_elements["dex"]["base"].value),
            "luk": int(dom_elements["luk"]["base"].value),

            "str_bonus": int(dom_elements["str"]["bonus"].value),
            "agi_bonus": int(dom_elements["agi"]["bonus"].value),
            "vit_bonus": int(dom_elements["vit"]["bonus"].value),
            "int_bonus": int(dom_elements["int"]["bonus"].value),
            "dex_bonus": int(dom_elements["dex"]["bonus"].value),
            "luk_bonus": int(dom_elements["luk"]["bonus"].value),

            "pow": int(dom_elements["pow"]["base"].value),
            "sta": int(dom_elements["sta"]["base"].value),
            "wis": int(dom_elements["wis"]["base"].value),
            "spl": int(dom_elements["spl"]["base"].value),
            "con": int(dom_elements["con"]["base"].value),
            "crt": int(dom_elements["crt"]["base"].value),

            "pow_bonus": int(dom_elements["pow"]["bonus"].value),
            "sta_bonus": int(dom_elements["sta"]["bonus"].value),
            "wis_bonus": int(dom_elements["wis"]["bonus"].value),
            "spl_bonus": int(dom_elements["spl"]["bonus"].value),
            "con_bonus": int(dom_elements["con"]["bonus"].value),
            "crt_bonus": int(dom_elements["crt"]["bonus"].value)
        }

        # 職業
        job_class: str = str(self.dom_elements["job_class"].value).strip()
        job_class_idx: int = None
        parent_direcoty: str = ""
        if "job_classes" in self.load_datas:
            ids = [idx for idx, value in enumerate(self.load_datas["job_classes"]) if value["class"] == job_class]
            if len(ids) > 0:
                job_class_idx = ids[0]
                if  "parent_directory" in self.load_datas["job_classes"][job_class_idx]:
                    parent_direcoty = self.load_datas["job_classes"][job_class_idx]["parent_directory"] + "/"

        if job_class_idx is None:
            # 正しいjobが選択されてない場合はreturn
            print("[WARNING]", f"Invalid job class: {job_class}")
            return

        # load HP table
        if self.load_datas["hp"] is None or self.job_class_idx != job_class_idx:
            response = requests.get(prefix_url + f"data/jobs/{parent_direcoty}{job_class}/hp.json", headers=self.headers)
            if response.status_code == 200:
                self.load_datas["hp"] = response.json()
            else:
                print("[WARNING]", "Get failed", "hp.json", response.status_code)
                self.load_datas["hp"] = {}

        # load SP table
        if self.load_datas["sp"] is None or self.job_class_idx != job_class_idx:
            response = requests.get(prefix_url + f"data/jobs/{parent_direcoty}{job_class}/sp.json", headers=self.headers)
            if response.status_code == 200:
                self.load_datas["sp"] = response.json()
            else:
                print("[WARNING]", "Get failed", "sp.json", response.status_code)
                self.load_datas["sp"] = {}

        # load weapon type table
        if self.load_datas["weapon_type"] is None or self.job_class_idx != job_class_idx:
            response = requests.get(prefix_url + f"data/jobs/{parent_direcoty}{job_class}/weapon_type.json", headers=self.headers)
            if response.status_code == 200:
                self.load_datas["weapon_type"] = response.json()
            else:
                print("[WARNING]", "Get failed", "weapon_type.json", response.status_code)
                self.load_datas["weapon_type"] = {}

        # 次回以降の処理のため記録
        self.job_class_name = job_class
        self.job_class_idx = job_class_idx
        self._valid = True

    def pre_calc(self) -> None:
        if self.is_valid() != True:
            return

        # Max HP
        hp_base_point: int = 0
        if "additional_info" in self.load_datas and "hp_base_point" in self.load_datas["additional_info"]:
            hp_base_point = self.load_datas["additional_info"]["hp_base_point"]
        else:
            hp_base_point = int(self.load_datas["hp"][str(self._point["base_lv"])])
        status_hp_max = int(hp_base_point + (hp_base_point * (self._point["vit"] + self._point["vit_bonus"]) / 100))
        self.dom_elements["hp_max"].value = status_hp_max

        # HP Recovery

        # Max SP
        sp_base_point: int = 0
        if "additional_info" in self.load_datas and "sp_base_point" in self.load_datas["additional_info"]:
            sp_base_point = self.load_datas["additional_info"]["sp_base_point"]
        else:
            sp_base_point = int(self.load_datas["sp"][str(self._point["base_lv"])])
        status_sp_max = int(sp_base_point + (sp_base_point * (self._point["int"] + self._point["int_bonus"]) / 100))
        self.dom_elements["sp_max"].value = status_sp_max

        # SP Recovery

        # Atk(not bow)
        status_atk = int((self._point["str"] + self._point["str_bonus"])
                + (self._point["dex"] + self._point["dex_bonus"]) * 0.2
                + (self._point["luk"] + self._point["luk_bonus"]) * 0.3
                )
        self.dom_elements["atk"]["base"].value = status_atk

        # Def
        status_def_base = int(self._point["base_lv"] * 0.5
                            + (self._point["agi"] + self._point["agi_bonus"]) * 0.2
                            + (self._point["vit"] + self._point["vit_bonus"]) * 0.5
                            )
        self.dom_elements["def"]["base"].value = status_def_base

        # Matk
        status_matk_base = int((self._point["int"] + self._point["int_bonus"])
                                + (self._point["dex"] + self._point["dex_bonus"]) * 0.2
                                + (self._point["luk"] + self._point["luk_bonus"]) * 0.3
                                )
        self.dom_elements["matk"]["base"].value = status_matk_base

        # Mdef
        status_mdef_base = int(self._point["base_lv"] * 0.2
                                + (self._point["int"] + self._point["int_bonus"])
                                + (self._point["vit"] + self._point["vit_bonus"]) * 0.2
                                + (self._point["dex"] + self._point["dex_bonus"]) * 0.2
                                )
        self.dom_elements["mdef"]["base"].value = status_mdef_base

        # Hit
        status_hit = int(175 + self._point["base_lv"]
                            + (self._point["dex"] + self._point["dex_bonus"])
                            + (self._point["luk"] + self._point["luk_bonus"]) * 0.3
                            )
        self.dom_elements["hit"].value = status_hit

        # Flee
        status_flee = int(100 + self._point["base_lv"]
                            + (self._point["agi"] + self._point["agi_bonus"])
                            + (self._point["luk"] + self._point["luk_bonus"]) * 0.2
                            )
        self.dom_elements["flee"].value = status_flee

        # 完全回避 : Complete avoidance
        status_complete_avoidance = 1 + int(((self._point["luk"] + self._point["luk_bonus"]) *0.1)*10)/10
        self.dom_elements["complete_avoidance"].value = status_complete_avoidance

        # Critical
        status_critical = int((1 + ((self._point["luk"] + self._point["luk_bonus"]) *0.3))*10)/10
        self.dom_elements["critical"].value = status_critical

        # Aspd(hand)
        aspd_base_point: int = 152
        aspd_penalty: float = (aspd_base_point - 144) / 50
        shield_correction_point: float = 0 #盾があれば-7～
        on_horseback_point: float = 1 #未騎乗
        #on_horseback_point: float = 0.5 + on_horseback_skill_lv * 0.1 #騎乗時
        status_aspd = int((aspd_base_point
                            + (math.sqrt(((self._point["agi"] + self._point["agi_bonus"]) * 3027 / 300)
                            + ((self._point["dex"] + self._point["dex_bonus"]) * 55 / 300)) * (1 - aspd_penalty)) + shield_correction_point) * on_horseback_point * 10)/10
        self.dom_elements["aspd"].value = status_aspd

    def calculation(self) -> None:
        pass
