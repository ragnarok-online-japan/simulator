# app.py
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
from io import BytesIO
from js import location,URLSearchParams,localStorage,window # type: ignore
from pyscript import document # type: ignore
import base64
import bz2
import json
import pyodide_http
import re
import requests
import traceback
import urllib.parse

from package.module_v1 import CalculationModule

pyodide_http.patch_all()

class Simulator:
    _initialized: bool = False
    _export_json_format_version: int = 1
    _prefix_url: str = "/"
    _suffix_url: str = "v1.html"

    _calculation_module: CalculationModule|None = None
    job_class_name: str|None = None

    dom_elements: dict = {}
    load_datas: dict = {
        "hp": None,
        "job_classese": None,
        "skill_list": {},
        "sp": None,
        "weapon_type": None,
    }

    status_primary: dict = {
        "str": {
            "status_window_position" : (256, 22)
        },
        "agi": {
            "status_window_position" : (256, 38)
        },
        "vit": {
            "status_window_position" : (256, 54)
        },
        "int": {
            "status_window_position" : (256, 70)
        },
        "dex": {
            "status_window_position" : (256, 86)
        },
        "luk": {
            "status_window_position" : (256, 102)
        }
    }
    status_talent: dict = {
        "pow": {
            "status_window_position" : (256, 142)
        },
        "sta": {
            "status_window_position" : (256, 158)
        },
        "wis": {
            "status_window_position" : (256, 174)
        },
        "spl": {
            "status_window_position" : (256, 190)
        },
        "con": {
            "status_window_position" : (256, 206)
        },
        "crt": {
            "status_window_position" : (256, 222)
        }
    }

    status_result: dict = {
        "atk": {
            "status_window_position" : (408, 26)
        },
        "def": {
            "status_window_position" : (494, 26)
        },
        "matk": {
            "status_window_position" : (408, 42)
        },
        "mdef": {
            "status_window_position" : (494, 42)
        },
        "hp_max": {},
        "hp_recovery": {},
        "sp_max": {},
        "sp_recovery": {},
        "hit": {
            "status_window_position" : (408, 58)
        },
        "flee": {
            "status_window_position" : (494, 58)
        },
        "complete_avoidance": {},
        "critical": {
            "status_window_position" : (408, 74)
        },
        "aspd": {
            "status_window_position" : (494, 74)
        },
        "weight_max":{}
    }

    headers={
        "Content-Type": "application/json",
        "Accept-Encoding": None, # delete unsafe header
        "Connection": None # delete unsafe header
    }

    def __init__(self, prefix_url: str, suffix_url: str|None = None, rood_url: str|None = None) -> None:
        self._prefix_url = prefix_url
        if suffix_url is not None:
            self._suffix_url = suffix_url
        if rood_url is not None:
            self._rood_url = rood_url

        # Base Lv
        self.dom_elements["base_lv"] = document.getElementById("status_base_lv")
        self.dom_elements["base_lv"].oninput = self.calculation

        # Job Lv
        self.dom_elements["job_lv"] = document.getElementById("status_job_lv")
        self.dom_elements["job_lv"].oninput = self.calculation

        # Job Class
        self.dom_elements["job_class"] = document.getElementById("status_job_class")
        self.dom_elements["job_class"].oninput = self.calculation

        # 基本ステータス
        for key in self.status_primary.keys():
            self.dom_elements[f"{key}_base"] = document.getElementById(f"status_{key}_base")
            self.dom_elements[f"{key}_base"].oninput = self.calculation

            self.dom_elements[f"{key}_bonus"] = document.getElementById(f"status_{key}_bonus")

        # 特性ステータス
        for key in self.status_talent.keys():
            self.dom_elements[f"{key}_base"] = document.getElementById(f"status_{key}_base")
            self.dom_elements[f"{key}_base"].oninput = self.calculation

            self.dom_elements[f"{key}_bonus"] = document.getElementById(f"status_{key}_bonus")

        # ステータス
        for key in self.status_result.keys():
            if key in  ("atk", "def", "matk", "mdef"):
                self.dom_elements[f"{key}_base"] = document.getElementById(f"status_{key}_base")
                self.dom_elements[f"{key}_bonus"] = document.getElementById(f"status_{key}_bonus")
            else:
                self.dom_elements[key] = document.getElementById(f"status_{key}")

        # 武器タイプ
        self.dom_elements["select_weapon_type_right"] = document.getElementById("select_weapon_type_right")
        self.dom_elements["select_weapon_type_left"]  = document.getElementById("select_weapon_type_left")

        self.dom_elements["input_character_name"] = document.getElementById("input_character_name")

        self.dom_elements["button_import_json"] = document.getElementById("button_import_json")
        self.dom_elements["button_import_json"].onclick = self.onclick_import_from_json

        self.dom_elements["textarea_import_json"] = document.getElementById("textarea_import_json")

        self.dom_elements["export_url"] = document.getElementById("export_url")
        self.dom_elements["export_url"].onclick = self.onclick_export_to_url

        self.dom_elements["dialog_button_close"] = document.getElementById("dialog_button_close")
        self.dom_elements["dialog_button_close"].onclick = self.close_dialog

        self.dom_elements["img_status_window"] = document.getElementById("img_status_window")

        self.dom_elements["button_draw_status_window"] = document.getElementById("button_draw_status_window")
        self.dom_elements["button_draw_status_window"].onclick = self.onclick_draw_status_window

        self.dom_elements["button_download_status_window"] = document.getElementById("button_download_status_window")
        self.dom_elements["button_download_status_window"].onclick = self.onclick_draw_status_window

        self.dom_elements["button_reset_data"] = document.getElementById("button_reset_data")
        self.dom_elements["button_reset_data"].onclick = self.onclick_reset_data

        # 職業情報
        response = requests.get(prefix_url + "data/job_classes.json", headers=self.headers)
        self.load_datas["job_classes"] = response.json()

        if len(self.load_datas["job_classes"]) > 0:
            datalist_job_classes = document.getElementById("datalist_job_classes")
            for idx, data in enumerate(self.load_datas["job_classes"]):
                option = document.createElement("option")
                option.value = data["class"]
                if "display_name" in data:
                    option.label = data["display_name"]

                datalist_job_classes.appendChild(option)

            self.dom_elements["job_class"].value = "novice"

        # スキル
        self.dom_elements["div_skills"] = document.getElementById("div_skills")
        self.dom_elements["skills"] = {}
        self.dom_elements["skill_lv"] = {}
        self.dom_elements["skill_enable"] = {}

        response = requests.get(self._prefix_url + f"data/skill_list.json", headers=self.headers)
        if response.status_code == 200:
            self.load_datas["skill_list"] = response.json()

        if len(self.load_datas["skill_list"]) > 0:
            response = requests.get(self._prefix_url + f"data/skill_list_update.json", headers=self.headers)
            if response.status_code == 200:
                skill_list_update = response.json()
                for key in skill_list_update.keys():
                    if key in self.load_datas["skill_list"]:
                        skill: dict = self.load_datas["skill_list"][key]
                        skill.update(skill_list_update[key])

            self.dom_elements["input_skill"] = document.getElementById("input_skill")
            button_skill_append = document.getElementById("button_skill_append")
            button_skill_append.onclick = self.onclick_skill_append

            datalist_skill = document.getElementById("datalist_skill")
            for idx, data in self.load_datas["skill_list"].items():
                if "name" not in data:
                    continue
                if data["name"] == "Unknown-Skill":
                    continue
                option = document.createElement("option")
                option.value = data["name"]
                option.setAttribute("data-skill-id", idx)

                datalist_skill.appendChild(option)

        # アイテム
        response = requests.get(self._prefix_url + f"data/items.json", headers=self.headers)
        if response.status_code == 200:
            self.load_datas["items"] = response.json()

        if len(self.load_datas["items"]) > 0:
            datalist_equipment_weapon_right = document.getElementById("datalist_equipment_weapon_right")
            datalist_equipment_weapon_left = document.getElementById("datalist_equipment_weapon_left")
            datalist_equipment_headgear_top = document.getElementById("datalist_equipment_headgear_top")
            datalist_equipment_headgear_center = document.getElementById("datalist_equipment_headgear_center")
            datalist_equipment_headgear_lower = document.getElementById("datalist_equipment_headgear_lower")
            datalist_equipment_shield = document.getElementById("datalist_equipment_shield")
            datalist_equipment_armour = document.getElementById("datalist_equipment_armour")
            datalist_equipment_shoulder = document.getElementById("datalist_equipment_shoulder")
            datalist_equipment_footwear = document.getElementById("datalist_equipment_footwear")
            datalist_equipment_accessory1 = document.getElementById("datalist_equipment_accessory1")
            datalist_equipment_accessory2 = document.getElementById("datalist_equipment_accessory2")

            response = requests.get(self._prefix_url + f"data/items_update.json", headers=self.headers)
            if response.status_code == 200:
                items_update = response.json()
                for key in items_update.keys():
                    if key in self.load_datas["items"]:
                        skill: dict = self.load_datas["items"][key]
                        skill.update(items_update[key])

            for idx, item in self.load_datas["items"].items():
                if "displayname" not in item or "type" not in item:
                    continue

                item_name = item["displayname"]
                if "slot" in item:
                    item_name = "{:s}[{:d}]".format(item_name, item["slot"])

                option = document.createElement("option")
                option.value = item_name
                option.setAttribute("data-item-id", idx)

                if item["type"] in ("短剣", "片手剣", "剣", "両手剣","カタール", "片手斧", "斧", "両手斧", "槍", "片手槍", "両手槍", "鈍器", "本", "弓", "投擲",
                                    "杖", "片手杖", "両手杖", "爪", "鞭", "楽器", "忍者刀", "風魔手裏剣", "銃", "ハンドガン", "ライフル", "ショットガン", "ガトリングガン", "グレネードガン"):
                    datalist_equipment_weapon_right.appendChild(option)

                    if item["type"] in ("短剣", "片手剣", "片手斧"):
                        option = option.cloneNode(True)
                        datalist_equipment_weapon_left.appendChild(option)

                elif item["type"] == "兜":
                    if "position" not in item:
                        pass
                    elif item["position"] == "上段":
                        datalist_equipment_headgear_top.appendChild(option)
                    elif item["position"] == "中段":
                        datalist_equipment_headgear_center.appendChild(option)
                    elif item["position"] == "下段":
                        datalist_equipment_headgear_lower.appendChild(option)
                    elif item["position"] == "上中下段":
                        datalist_equipment_headgear_top.appendChild(option)
                    elif item["position"] == "上下段":
                        datalist_equipment_headgear_top.appendChild(option)

                elif item["type"] == "盾":
                    datalist_equipment_shield.appendChild(option)

                elif item["type"] == "鎧":
                    datalist_equipment_armour.appendChild(option)

                elif item["type"] == "肩にかける物":
                    datalist_equipment_shoulder.appendChild(option)

                elif item["type"] == "靴":
                    datalist_equipment_footwear.appendChild(option)

                elif item["type"] == "アクセサリー":
                    datalist_equipment_accessory1.appendChild(option)
                    option = option.cloneNode(True)
                    datalist_equipment_accessory2.appendChild(option)

                elif item["type"] == "アクセサリー(1)":
                    datalist_equipment_accessory1.appendChild(option)

                elif item["type"] == "アクセサリー(2)":
                    datalist_equipment_accessory2.appendChild(option)
                else:
                    print(item["type"])

        # セーブ/ロード
        div_save_load = document.getElementById("div_save_load")
        alert_unavailable_save_load = document.getElementById("alert_unavailable_save_load")
        if window.localStorage:
            # localStorage 対応Browser
            alert_unavailable_save_load.hidden = True
            div_save_load.hidden = False

            self.dom_elements["select_slot_savelist"] = document.getElementById("select_slot_savelist")
            self.dom_elements["select_slot_savelist"].onchange = self.onclick_slot_select
            slot_size: int = localStorage.length
            if slot_size > 0:
                pattern = re.compile(r"^simulator\.json\.(.+)$")
                for idx in range(slot_size):
                    key: str = localStorage.key(idx)
                    matches = pattern.match(key)
                    if matches == None:
                        continue
                    print("[TRACE]", "localStorage, key:", key)

                    slot_name: str = matches.group(1)
                    option = document.createElement("option")
                    option.value = key
                    option.label = slot_name

                    self.dom_elements["select_slot_savelist"].appendChild(option)

            self.dom_elements["button_slot_save"] = document.getElementById("button_slot_save")
            self.dom_elements["button_slot_save"].onclick = self.onclick_slot_save

            self.dom_elements["button_slot_load"] = document.getElementById("button_slot_load")
            self.dom_elements["button_slot_load"].onclick = self.onclick_slot_load

            self.dom_elements["button_slot_delete"] = document.getElementById("button_slot_delete")
            self.dom_elements["button_slot_delete"].onclick = self.onclick_slot_delete
        else:
            # localStorage 未対応Browser
            alert_unavailable_save_load.hidden = False
            div_save_load.hidden = True

        # initilzed finish
        self._initialized = True

    def onclick_reset_data(self, event = None) -> None:
        self.reset_data()
        self.calculation()
        self.draw_img_status_window()
        self.view_dialog("リセットが完了しました")

    def reset_data(self) -> None:
        self._initialized = False

        print("[TRACE]", "Reset data")

        self.dom_elements["base_lv"].value = 1

        self.dom_elements["job_lv"].value = 1

        self.dom_elements["job_class"].value = "novice"

        self.dom_elements["input_character_name"].value = "Simulator"

        document.getElementById("textarea_description").value = ""

        # 基本ステータス
        for key in self.status_primary.keys():
            self.dom_elements[f"{key}_base"].value = 1
            self.dom_elements[f"{key}_bonus"].value = 0

        # 特性ステータス
        for key in self.status_talent.keys():
            self.dom_elements[f"{key}_base"].value = 0
            self.dom_elements[f"{key}_bonus"].value = 0

        # ステータス
        for key in self.status_result.keys():
            if key in  ("atk", "def", "matk", "mdef"):
                self.dom_elements[f"{key}_base"].value = 1
                self.dom_elements[f"{key}_bonus"].value = 0
            else:
                self.dom_elements[key].value = 1

        # スキル
        self.dom_elements["skill_lv"].clear()
        self.dom_elements["skill_enable"].clear()
        for key in self.dom_elements["skills"].keys():
            self.dom_elements["skills"][key].remove()
        self.dom_elements["skills"].clear()

        if "additional_info" in self.load_datas:
            if "hp_base_point" in self.load_datas["additional_info"]:
                del self.load_datas["additional_info"]["hp_base_point"]
            if "sp_base_point" in self.load_datas["additional_info"]:
                del self.load_datas["additional_info"]["sp_base_point"]

        # initilzed finish
        self._initialized = True

    def onclick_import_from_json(self, event = None) -> None:
        try:
            self.import_from_json(self.dom_elements["textarea_import_json"].value)
            self.calculation()
            self.draw_img_status_window()
            self.view_dialog("JSONからインポートしました")
        except Exception as ex:
            traceback.print_exception(ex)
            self.view_dialog(f"*** ERROR ***\nJSONからのインポートに失敗しました\n{ex}")

    def import_from_json(self, data_json: str) -> None:
        format_version: int = 0
        try:
            data_dict = json.loads(data_json)
        except json.decoder.JSONDecodeError as ex:
            raise Exception("JSONフォーマットが不正です")

        if "format_version" in data_dict:
            try:
                format_version = int(data_dict["format_version"])
            except ValueError:
                pass

        if format_version is None or format_version > self._export_json_format_version:
            raise Exception(f"未知のJSONフォーマットVersionです\n入力されたフォーマットVersion:{format_version}")

        if "status" in data_dict:
            if "base_lv" in data_dict["status"]:
                self.dom_elements["base_lv"].value = data_dict["status"]["base_lv"]

            if "job_lv" in data_dict["status"]:
                self.dom_elements["job_lv"].value = data_dict["status"]["job_lv"]

            if "job_class" in data_dict["status"]:
                self.dom_elements["job_class"].value = data_dict["status"]["job_class"]

            for key in self.status_primary.keys():
                if key in data_dict["status"]:
                    self.dom_elements[f"{key}_base"].value = data_dict["status"][key]

            for key in self.status_talent.keys():
                if key in data_dict["status"]:
                    self.dom_elements[f"{key}_base"].value = data_dict["status"][key]

        if "skills" in data_dict:
            for key in data_dict["skills"].keys():
                self.append_skill_row(key, data_dict["skills"][key])

        if "equipments" in data_dict:
            pass

        if "additional_info" in data_dict:
            if "character_name" in data_dict["additional_info"]:
                self.dom_elements["input_character_name"].value = data_dict["additional_info"]["character_name"]

            if "additional_info" not in self.load_datas:
                self.load_datas["additional_info"] = {} #init

            if "hp_base_point" in data_dict["additional_info"]:
                try:
                    self.load_datas["additional_info"]["hp_base_point"] = int(data_dict["additional_info"]["hp_base_point"])
                except ValueError:
                    pass
            if "sp_base_point" in data_dict["additional_info"]:
                try:
                    self.load_datas["additional_info"]["sp_base_point"] = int(data_dict["additional_info"]["sp_base_point"])
                except ValueError:
                    pass

    def onclick_skill_append(self, event = None) -> None:
        skill_name: str = self.dom_elements["input_skill"].value
        skill_option = document.querySelector(f"#datalist_skill option[value='{skill_name}']")

        skill_id: str|None = None
        if skill_option is None:
            print("[WARNING]", f"Unknown skill: {skill_name}")
            self.dom_elements["input_skill"].value = ""
            return
        else:
            skill_id = skill_option.getAttribute("data-skill-id")

        if skill_id in self.dom_elements["skills"]:
            # 追加済み
            pass
        elif skill_id in self.load_datas["skill_list"]:
            data = {}
            self.append_skill_row(skill_id, data)

        self.dom_elements["input_skill"].value = ""

        self.calculation()
        self.draw_img_status_window()

    def append_skill_row(self, skill_id: str|None, data: dict) -> None:
        if skill_id not in self.load_datas["skill_list"]:
            print("[WARNING]", f"Unknown skill: {skill_id}")
            return

        if "lv" not in data:
            data["lv"] = 0

        lv: int = 0
        try:
            lv = int(data["lv"])
        except ValueError:
            pass

        skill_name: str = self.load_datas["skill_list"][skill_id]["name"]
        max_lv: int = self.load_datas["skill_list"][skill_id]["max_lv"]
        buff: bool = False
        if "buff" in self.load_datas["skill_list"][skill_id] and self.load_datas["skill_list"][skill_id]["buff"] == True:
            buff = True

        div_row = document.createElement("div")
        div_row.setAttribute("id", f"skill.{skill_id}")
        div_row.setAttribute("class", "row border border-secondary rounded")

        div_col1 = document.createElement("div")
        div_col1.setAttribute("class", "col-md-4")
        div_row.appendChild(div_col1)

        skill_label = document.createElement("label")
        skill_label.setAttribute("class", "form-label")
        skill_label.setAttribute("for", f"skill_lv.{skill_id}")
        skill_label.innerText = skill_name
        div_col1.appendChild(skill_label)

        div_col2 = document.createElement("div")
        div_col2.setAttribute("class", "col-md-2")
        div_col2.innerText = "Lv:"
        div_row.appendChild(div_col2)

        skill_lv = document.createElement("input")
        skill_lv.setAttribute("id", f"skill_lv.{skill_id}")
        skill_lv.setAttribute("class", "form-number skill-lv")
        skill_lv.setAttribute("type", "number")
        skill_lv.setAttribute("name", skill_id)
        skill_lv.setAttribute("min", 0)
        skill_lv.setAttribute("max", max_lv)
        skill_lv.setAttribute("value", lv)
        div_col2.appendChild(skill_lv)

        div_col3 = document.createElement("div")
        div_col3.setAttribute("class", "col-md-2")
        div_row.appendChild(div_col3)

        skill_enable = None
        if buff == True:
            skill_enabled_label = document.createElement("label")
            skill_enabled_label.setAttribute("for", f"skill_enable.{skill_id}")
            skill_enabled_label.innerText = "Enable:"
            div_col3.appendChild(skill_enabled_label)

            skill_enable = document.createElement("input")
            skill_enable.setAttribute("id", f"skill_enable.{skill_id}")
            skill_enable.setAttribute("class", "form-check-input")
            skill_enable.setAttribute("type", "checkbox")
            skill_enable.setAttribute("name", skill_id)
            if "enable" in data and data["enable"] == False:
                skill_enable.setAttribute("checked", "")
            elif lv > 0:
                skill_enable.setAttribute("checked", "checked")
            div_col3.appendChild(skill_enable)

        div_col4 = document.createElement("div")
        div_col4.setAttribute("class", "col-md-4")
        div_row.appendChild(div_col4)

        skill_remove = document.createElement("button")
        skill_remove.setAttribute("type", "button")
        skill_remove.setAttribute("class", "btn-close")
        skill_remove.setAttribute("arial-label", "Remove")
        skill_remove.setAttribute("data-skill-id", skill_id)
        skill_remove.onclick = self.onclick_skill_remove
        div_col4.appendChild(skill_remove)

        self.dom_elements["div_skills"].appendChild(div_row)

        self.dom_elements["skills"][skill_id] = div_row
        self.dom_elements["skill_lv"][skill_id] = skill_lv
        if skill_enable is not None:
            self.dom_elements["skill_enable"][skill_id] = skill_enable

    def onclick_skill_remove(self, event = None) -> None:
        if event is None:
            return

        skill_id: str = event.target.getAttribute("data-skill-id")

        # スキル
        self.dom_elements["skill_lv"][skill_id].remove()
        del self.dom_elements["skill_lv"][skill_id]
        if skill_id in self.dom_elements["skill_enable"]:
            self.dom_elements["skill_enable"][skill_id].remove()
            del self.dom_elements["skill_enable"][skill_id]
        self.dom_elements["skills"][skill_id].remove()
        del self.dom_elements["skills"][skill_id]

        self.calculation()
        self.draw_img_status_window()

    def import_from_base65536(self, data_base64: str) -> bool:
        success: bool = False
        try:
            data_compressed = base64.urlsafe_b64decode(data_base64)
            data_json = bz2.decompress(data_compressed)
            self.dom_elements["textarea_import_json"].value = data_json.decode("utf-8")
            self.import_from_json(data_json.decode("utf-8"))
            success = True
        except Exception as ex:
            traceback.print_exception(ex)

        return success

    def export_to_json(self) -> str:
        data_json: dict = {
            "format_version" : self._export_json_format_version,
            "status" : {
                "base_lv" : int(self.dom_elements["base_lv"].value),
                "job_lv" : int(self.dom_elements["job_lv"].value),
                "job_class": self.dom_elements["job_class"].value
            },
            "skills": {

            },
            "equipments": {

            },
            "items": {

            },
            "supports": {

            },
            "additional_info": {
                "character_name": self.dom_elements["input_character_name"].value
            }
        }

        for key in self.status_primary.keys():
            value: int = 0
            try:
                value = int(self.dom_elements[f"{key}_base"].value)
            except ValueError:
                pass

            data_json["status"][key] = value

        for key in self.status_talent.keys():
            if f"{key}_base" in self.dom_elements:
                value: int = 0
                try:
                    value = int(self.dom_elements[f"{key}_base"].value)
                except ValueError:
                    pass

                if value > 0:
                    data_json["status"][key] = value

        for key in self.dom_elements["skill_lv"].keys():
            value: int = 0
            try:
                value = int(self.dom_elements["skill_lv"][key].value)
            except ValueError:
                pass

            enable: bool = False
            if key in self.dom_elements["skill_enable"] and self.dom_elements["skill_enable"][key].checked == True:
                enable = True

            data_json["skills"][key] = {
                "lv": value,
                "enable": enable
            }

        if "additional_info" in self.load_datas:
            for key in self.load_datas["additional_info"]:
                data_json["additional_info"][key] = self.load_datas["additional_info"][key]

        # dict => json
        data_json_str: str = json.dumps(data_json, ensure_ascii=False, indent=4)

        self.dom_elements["textarea_import_json"].value = data_json_str

        return data_json_str

    def export_to_url(self) -> str:
        data_json: str = self.export_to_json()

        # json => bz2 copressed
        data_compressed = bz2.compress(data_json.encode("utf-8"), compresslevel=9)

        # bz2 compressed => base64
        data_base64 = base64.urlsafe_b64encode(data_compressed).decode("utf-8")

        url = self._prefix_url + self._suffix_url + "?" + data_base64 + "#main"
        return url

    def onclick_export_to_url(self, event = None) -> None:
        url = self.export_to_url()
        window.open(url)

    def onclick_slot_select(self, event = None) -> None:
        if event is None:
            return

        key_description = str(event.currentTarget.value).replace("simulator.json.", "simulator.description.", 1)
        description = localStorage.getItem(key_description)
        if description is not None:
            alert_slot_description = document.getElementById("alert_slot_description")
            alert_slot_description.hidden = False
            alert_slot_description.innerText = description

    def onclick_slot_save(self, event = None) -> None:
        character_name: str = self.dom_elements["input_character_name"].value
        if len(character_name) == 0:
            self.view_dialog("キャラクターネームを最低１文字以上設定してください")
            return

        job_class: str = str(self.dom_elements["job_class"].value).capitalize()
        dt_now = str(datetime.now().replace(microsecond=0))
        slot_name: str = f"Name:{character_name}, Job:{job_class}, ({dt_now})"
        key: str = f"simulator.json.{slot_name}"
        option = document.createElement("option")
        option.value = key
        option.label = slot_name
        self.dom_elements["select_slot_savelist"].appendChild(option)

        data_json: str = self.export_to_json()
        print("[INFO]", "Save localStorage, key:", key)
        localStorage.setItem(key, data_json)

        key_description: str = f"simulator.description.{slot_name}"
        print("[INFO]", "Save localStorage, key:", key)
        localStorage.setItem(key_description, document.getElementById("textarea_description").value)
        self.view_dialog("セーブが完了しました")

    def onclick_slot_load(self, event = None) -> None:
        idx: int = self.dom_elements["select_slot_savelist"].selectedIndex
        if idx < 0:
            return

        key: str = self.dom_elements["select_slot_savelist"].value
        key_description = key.replace("simulator.json.", "simulator.description.", 1)

        print("[INFO]", "Load localStorage, key:", key)
        data_json: str = localStorage.getItem(key)
        if data_json is not None:
            self.reset_data()

            print("[INFO]", "Load localStorage, key:", key_description)
            description = localStorage.getItem(key_description)
            if description is not None:
                document.getElementById("textarea_description").value = description

            self.import_from_json(data_json)
            self.calculation()
            self.draw_img_status_window()
            self.view_dialog("ロードが完了しました")

    def onclick_slot_delete(self, event = None) -> None:
        idx: int = self.dom_elements["select_slot_savelist"].selectedIndex
        if idx < 0:
            return
        key: str = self.dom_elements["select_slot_savelist"].value
        self.dom_elements["select_slot_savelist"].remove(idx)

        alert_slot_description = document.getElementById("alert_slot_description")
        alert_slot_description.hidden = True

        # Delete JSON
        print("[INFO]", "Delete localStorage, key:", key)
        localStorage.removeItem(key)

        # Delete description
        key_description = key.replace("simulator.json.", "simulator.description.", 1)
        print("[INFO]", "Delete localStorage, key:", key_description)
        localStorage.removeItem(key_description)

    def calculation(self, event = None) -> bool:
        if self._initialized != True:
            # initialize未完了の場合終了
            return False

        try:
            # calculation
            job_class_name = self.dom_elements["job_class"].value.strip()
            if self._calculation_module is None \
                or (self.job_class_name is not None and self.job_class_name != job_class_name):
                # Re-initalize
                self._calculation_module = CalculationModule(self._prefix_url, self.dom_elements, self.load_datas)

            if self._calculation_module.is_valid() == True:
                # save
                self.job_class_name = job_class_name

                job_class_idx = self._calculation_module.get_job_class_idx()
                job_data = self.load_datas["job_classes"][job_class_idx]

                maximum = job_data["base_lv_max"]
                self.dom_elements["base_lv"].max = maximum
                if int(self.dom_elements["base_lv"].value) > maximum:
                    self.dom_elements["base_lv"].value = maximum

                maximum = job_data["job_lv_max"]
                self.dom_elements["job_lv"].max = maximum
                if int(self.dom_elements["job_lv"].value) > maximum:
                    self.dom_elements["job_lv"].value = maximum

                maximum = job_data["base_point_max"]
                for key in self.status_primary.keys():
                    self.dom_elements[f"{key}_base"].max = maximum
                    if int(self.dom_elements[f"{key}_base"].value) > maximum:
                        self.dom_elements[f"{key}_base"].value = maximum

                maximum = job_data["talent_point_max"]
                for key in self.status_talent.keys():
                    self.dom_elements[f"{key}_base"].max = maximum
                    if int(self.dom_elements[f"{key}_base"].value) > maximum:
                        self.dom_elements[f"{key}_base"].value = maximum

                # 計算前の準備
                self._calculation_module.pre_calc()

                # 計算
                self._calculation_module.calculation()

        except Exception as ex:
            traceback.print_exception(ex)
            return False
        else:
            self.export_to_json()
            return True

    def onclick_draw_status_window(self, event = None):
        self.calculation()
        self.draw_img_status_window()

    def draw_img_status_window(self, img_src: str = "./assets/img/statwin_bg.png"):
        img = Image.open(img_src)
        font_lg = ImageFont.truetype("./assets/font/SourceHanCodeJP-Medium.otf", size=10)
        font_md = ImageFont.truetype("./assets/font/SourceHanCodeJP-Medium.otf", size=9)
        font_logo = ImageFont.truetype("./assets/font/SourceHanCodeJP-Medium.otf", size=8)
        draw = ImageDraw.Draw(img)

        draw.text((0,200), "Powerd by\n Ragnarok Online Japan Simulator", "#16507b", font=font_logo, align="left")

        draw.text((20,1), "基本情報", "#000000", font=font_lg, align="left")
        draw.text((236,1), "ステータス", "#000000", font=font_lg, align="left")
        draw.text((236,122), "特性ステータス", "#000000", font=font_lg, align="left")

        character_name: str = self.dom_elements["input_character_name"].value
        draw.text((10,20), character_name, "#000000", font=font_lg, align="left")
        draw.text((10,36), str(self.dom_elements["job_class"].value).capitalize(), "#000000", font=font_md, align="left")

        draw.text((16,50), "HP", "#000000", font=font_md, align="left")
        hp_max = self.dom_elements["hp_max"].value
        draw.text((100,50), f"{hp_max} / {hp_max}", "#000000", font=font_md, align="center", anchor="ma")

        draw.text((16,66), "SP", "#000000", font=font_md, align="left")
        sp_max = self.dom_elements["sp_max"].value
        draw.text((100,66), f"{sp_max} / {sp_max}", "#000000", font=font_md, align="center", anchor="ma")

        draw.text((16,100), "Base Lv. " + self.dom_elements["base_lv"].value, "#000000", font=font_md, align="left")
        draw.text((16,112), "Job Lv. " + self.dom_elements["job_lv"].value, "#000000", font=font_md, align="left")

        weight_max: str = self.dom_elements["weight_max"].value
        zeny: int = 1
        draw.text((216,134), f"Weight:0/{weight_max} | Zeny:{zeny:,d}", "#000000", font=font_md, align="right", anchor="ra")

        for key in self.status_primary.keys():
            text = self.dom_elements[f"{key}_base"].value
            text += "+"
            text += self.dom_elements[f"{key}_bonus"].value
            position = self.status_primary[key]["status_window_position"]
            draw.text(position, text, "#000000", font=font_md, align="left")

        for key in self.status_talent.keys():
            text = self.dom_elements[f"{key}_base"].value
            text += "+"
            text += self.dom_elements[f"{key}_bonus"].value
            position = self.status_talent[key]["status_window_position"]
            draw.text(position, text, "#000000", font=font_md, align="left")

        for key in self.status_result.keys():
            if "status_window_position" in self.status_result[key]:
                text: str = ""
                if key in  ("atk", "def", "matk", "mdef"):
                    text = self.dom_elements[f"{key}_base"].value
                    text += " + "
                    text += self.dom_elements[f"{key}_bonus"].value
                elif key == "flee":
                    text = self.dom_elements[key].value
                    text += " + "
                    text += "{:.0f}".format(float(self.dom_elements["complete_avoidance"].value))
                elif key in ("critical", "aspd"):
                    text = "{:.0f}".format(float(self.dom_elements[key].value))
                else:
                    text = self.dom_elements[key].value

                position = self.status_result[key]["status_window_position"]
                draw.text(position, text, "#000000", font=font_md, align="right", anchor="rt")

        # zoom x2
        img = img.resize((img.width * 2, img.height * 2))

        buffer = BytesIO()
        img.save(buffer, "png")
        img_str = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
        img_status_window = self.dom_elements["img_status_window"]
        img_status_window.src = img_str
        img_status_window.width = img.width
        img_status_window.height = img.height

        # Download
        button_download_status_window = self.dom_elements["button_download_status_window"]
        button_download_status_window.href = img_str

    def view_dialog(self, message: str = "") -> None:
        message_div = document.getElementById("dialog_information_message_div")
        message_div.innerText = message

        dialog = document.getElementById("dialog")
        dialog.showModal()

    def close_dialog(self, event = None) -> None:
        dialog = document.getElementById("dialog")
        dialog.close()

def main():
    query_strings = URLSearchParams.new(location.search)

    prefix_url: str = f"{location.protocol}//{location.host}/simulator/"
    instance = Simulator(prefix_url)

    result_import: bool|None = None
    if str(query_strings) != "":
        data_base_encoded = urllib.parse.unquote(str(query_strings))
        result_import = instance.import_from_base65536(data_base_encoded[:-1])

    execute_calculation: bool = True
    if result_import is not None:
        if result_import == True:
            instance.view_dialog("インポートが完了しました")
        else:
            instance.view_dialog("*** ERROR ***\nインポートが失敗しました")
            execute_calculation = False

    if execute_calculation == True:
        instance.calculation()
        instance.draw_img_status_window()

    # preloader
    preloader = document.getElementById("preloader")
    if preloader:
        preloader.remove()

if __name__ == "__main__":
    main()
