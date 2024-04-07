import math
import traceback
from lark import Lark

import requests

from package.visitor import Visitor, Environment
from package.abstract_module import AbstractCalculationModule

class CalculationModule(AbstractCalculationModule):
    _memory: dict = {}

    def __init__(self, prefix_url: str, dom_elements: dict[str], load_datas: dict[str]) -> None:
        # init
        self._valid = False

        self.prefix_url = prefix_url
        self.dom_elements = dom_elements
        self.load_datas = load_datas

        try:
            self._memory["base_lv"] = int(dom_elements["base_lv"].value)
            self._memory["job_lv"] = int(dom_elements["base_lv"].value)

            for key in self.status_primary:
                for sub in ("base", "bonus"):
                    self._memory[f"{key}_{sub}"] = int(dom_elements[f"{key}_{sub}"].value)

            for key in self.status_talent:
                for sub in ("base", "bonus"):
                    self._memory[f"{key}_{sub}"] = int(dom_elements[f"{key}_{sub}"].value)

        except ValueError:
            pass

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

        # Lark
        rule = open("./package/grammer.lark").read()
        self.lark_parser = Lark(rule, start="program", parser="lalr")
        self.visitor = Visitor()

        self._valid = True

    def pre_calc(self) -> None:
        if self.is_valid() != True:
            return

        # 装備, スキルなどの事前処理

    def calculation(self) -> None:
        # Max HP
        hp_base_point: int = 0
        if "additional_info" in self.load_datas and "hp_base_point" in self.load_datas["additional_info"]:
            hp_base_point = self.load_datas["additional_info"]["hp_base_point"]
        else:
            hp_base_point = int(self.load_datas["hp"][str(self._memory["base_lv"])])
        self._memory["hp_max"] = int(hp_base_point + (hp_base_point * (self._memory["vit_base"] + self._memory["vit_bonus"]) / 100))
        self.dom_elements["hp_max"].value = self._memory["hp_max"]

        # HP Recovery

        # Max SP
        sp_base_point: int = 0
        if "additional_info" in self.load_datas and "sp_base_point" in self.load_datas["additional_info"]:
            sp_base_point = self.load_datas["additional_info"]["sp_base_point"]
        else:
            sp_base_point = int(self.load_datas["sp"][str(self._memory["base_lv"])])
        self._memory["sp_max"] = int(sp_base_point + (sp_base_point * (self._memory["int_base"] + self._memory["int_bonus"]) / 100))
        self.dom_elements["sp_max"].value = self._memory["sp_max"]

        # SP Recovery

        # Atk(not bow)
        self._memory["atk_base"] = int((self._memory["str_base"] + self._memory["str_bonus"])
                + (self._memory["dex_base"] + self._memory["dex_bonus"]) * 0.2
                + (self._memory["luk_base"] + self._memory["luk_bonus"]) * 0.3
                )
        self.dom_elements["atk_base"].value = self._memory["atk_base"]

        self._memory["atk_bonus"] = 0
        self.dom_elements["atk_bonus"].value = self._memory["atk_bonus"]

        # Def
        self._memory["def_base"] = int(self._memory["base_lv"] * 0.5
                            + (self._memory["agi_base"] + self._memory["agi_bonus"]) * 0.2
                            + (self._memory["vit_base"] + self._memory["vit_bonus"]) * 0.5
                            )
        self.dom_elements["def_base"].value = self._memory["def_base"]

        self._memory["def_bonus"] = 0
        self.dom_elements["def_bonus"].value = self._memory["def_bonus"]

        # Matk
        self._memory["matk_base"] = int((self._memory["int_base"] + self._memory["int_bonus"])
                                + (self._memory["dex_base"] + self._memory["dex_bonus"]) * 0.2
                                + (self._memory["luk_base"] + self._memory["luk_bonus"]) * 0.3
                                )
        self.dom_elements["matk_base"].value = self._memory["matk_base"]

        self._memory["matk_bonus"] = 0
        self.dom_elements["matk_bonus"].value = self._memory["matk_bonus"]

        # Mdef
        self._memory["mdef_base"] = int(self._memory["base_lv"] * 0.2
                                + (self._memory["int_base"] + self._memory["int_bonus"])
                                + (self._memory["vit_base"] + self._memory["vit_bonus"]) * 0.2
                                + (self._memory["dex_base"] + self._memory["dex_bonus"]) * 0.2
                                )
        self.dom_elements["mdef_base"].value = self._memory["mdef_base"]

        self._memory["mdef_bonus"] = 0
        self.dom_elements["mdef_bonus"].value = self._memory["mdef_bonus"]

        # Hit
        self._memory["hit"] = int(175 + self._memory["base_lv"]
                            + (self._memory["dex_base"] + self._memory["dex_bonus"])
                            + (self._memory["luk_base"] + self._memory["luk_bonus"]) * 0.3
                            )
        self.dom_elements["hit"].value = self._memory["hit"]

        # Flee
        self._memory["flee"] = int(100 + self._memory["base_lv"]
                            + (self._memory["agi_base"] + self._memory["agi_bonus"])
                            + (self._memory["luk_base"] + self._memory["luk_bonus"]) * 0.2
                            )
        self.dom_elements["flee"].value = self._memory["flee"]

        # 完全回避 : Complete avoidance
        self._memory["complete_avoidance"] = 1 + int(((self._memory["luk_base"] + self._memory["luk_bonus"]) *0.1)*10)/10
        self.dom_elements["complete_avoidance"].value = self._memory["complete_avoidance"]

        # Critical
        self._memory["critical"] = int((1 + ((self._memory["luk_base"] + self._memory["luk_bonus"]) *0.3))*10)/10
        self.dom_elements["critical"].value = self._memory["critical"]

        # Aspd(hand)
        aspd_base_point: int = 152
        aspd_penalty: float = (aspd_base_point - 144) / 50
        shield_correction_point: float = 0 #盾があれば-7～
        on_horseback_point: float = 1 #未騎乗
        #on_horseback_point: float = 0.5 + on_horseback_skill_lv * 0.1 #騎乗時
        status_aspd = int((aspd_base_point
                            + (math.sqrt(((self._memory["agi_base"] + self._memory["agi_bonus"]) * 3027 / 300)
                            + ((self._memory["dex_base"] + self._memory["dex_bonus"]) * 55 / 300)) * (1 - aspd_penalty)) + shield_correction_point) * on_horseback_point * 10)/10
        self.dom_elements["aspd"].value = status_aspd

        code:str = ""
        try:
            tree = self.lark_parser.parse(code)
            env = Environment(self._memory)
            self.visitor.visit(tree, env)
        except Exception as ex:
            traceback.print_exception(ex)
