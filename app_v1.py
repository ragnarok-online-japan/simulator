# app.py
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from js import location,URLSearchParams,localStorage
from pyscript import document
import base64
import binascii
import bz2
import json
import pyodide_http
import requests
import traceback
import urllib.parse
pyodide_http.patch_all()

import package


class Simulator:
    _initialized: bool = False
    _export_json_format_version: int = 1
    _prefix_url: str = "/"
    _suffix_url: str = "index.html"

    dom_elements: dict[str] = {}
    load_datas: dict[str] = {}

    _status_primary: dict = {
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
    _status_talent: dict = {
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

    _status_result: dict = {
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

    def __init__(self, prefix_url = "/", suffix_url="index.html") -> None:
        self._prefix_url = prefix_url
        self._suffix_url = suffix_url

        self.dom_elements["base_lv"] = document.getElementById("status_base_lv")
        self.dom_elements["base_lv"].oninput = self.calculation

        self.dom_elements["job_lv"] = document.getElementById("status_job_lv")
        self.dom_elements["job_lv"].oninput = self.calculation

        self.dom_elements["job_class"] = document.getElementById("status_job_class")
        self.dom_elements["job_class"].oninput = self.calculation

        # 基本ステータス
        for key in self._status_primary.keys():
            self.dom_elements[key]: dict = {
                "base"  : document.getElementById(f"status_{key}_base"),
                "bonus" : document.getElementById(f"status_{key}_bonus"),
            }
            self.dom_elements[key]["base"].oninput = self.calculation

        # 特性ステータス
        for key in self._status_talent.keys():
            self.dom_elements[key]: dict = {
                "base"  : document.getElementById(f"status_{key}_base"),
                "bonus" : document.getElementById(f"status_{key}_bonus"),
            }
            self.dom_elements[key]["base"].oninput = self.calculation

        # ステータス
        for key in self._status_result.keys():
            if key in  ("atk", "def", "matk", "mdef"):
                self.dom_elements[key]: dict = {
                    "base"  : document.getElementById(f"status_{key}_base"),
                    "bonus" : document.getElementById(f"status_{key}_bonus"),
                }
            else:
                self.dom_elements[key] = document.getElementById(f"status_{key}")

        # 武器タイプ
        self.dom_elements["select_weapon_type_right"] = document.getElementById("select_weapon_type_right")
        self.dom_elements["select_weapon_type_left"]  = document.getElementById("select_weapon_type_left")

        self.dom_elements["input_character_name"] = document.getElementById("input_character_name")

        self.dom_elements["button_import_json"] = document.getElementById("button_import_json")
        self.dom_elements["button_import_json"].onclick = self.onclick_import_from_json

        self.dom_elements["textarea_import_json"] = document.getElementById("textarea_import_json")

        self.dom_elements["daialog_button_close"] = document.getElementById("daialog_button_close")
        self.dom_elements["daialog_button_close"].onclick = self.close_dialog

        self.dom_elements["img_status_window"] = document.getElementById("img_status_window")

        self.dom_elements["button_draw_status_window"] = document.getElementById("button_draw_status_window")
        self.dom_elements["button_draw_status_window"].onclick = self.onclick_draw_status_window

        self.dom_elements["button_download_status_window"] = document.getElementById("button_download_status_window")
        self.dom_elements["button_download_status_window"].onclick = self.onclick_draw_status_window

        self.dom_elements["button_reset_data"] = document.getElementById("button_reset_data")
        self.dom_elements["button_reset_data"].onclick = self.onclick_reset_data

        # 職業情報
        headers={
            "Content-Type": "application/json",
            "Accept-Encoding": None, # delete unsafe header
            "Connection": None # delete unsafe haader
        }
        response = requests.get(prefix_url + "data/job_classes.json", headers=headers)
        self.load_datas["job_classes"] = response.json()

        if len(self.load_datas["job_classes"]) > 0:
            datalist_job_classes = document.getElementById("datalist_job_classes")
            for idx in self.load_datas["job_classes"]:
                child_class = document.createElement("option")
                data = self.load_datas["job_classes"][idx]

                child_class.value = data["class"]
                if "display_name" in data:
                    child_class.label = data["display_name"]

                datalist_job_classes.appendChild(child_class)

            self.dom_elements["job_class"].value = "novice"

        # initilzed finish
        self._initialized = True

    def onclick_reset_data(self, event = None) -> None:
        self.reset_data()
        self.calculation()
        self.draw_img_status_window()
        self.view_dialog("リセットが完了しました")

    def reset_data(self) -> None:
        self.dom_elements["base_lv"].value = 1

        self.dom_elements["job_lv"].value = 1

        self.dom_elements["job_class"].value = "novice"

        self.dom_elements["input_character_name"].value = "フェニックス1号"

        # 基本ステータス
        for key in self._status_primary.keys():
            self.dom_elements[key]["base"].value = 1

        # 特性ステータス
        for key in self._status_talent.keys():
            self.dom_elements[key]["base"].value = 1

    def onclick_import_from_json(self, event = None) -> None:
        try:
            self.import_from_json(self.dom_elements["textarea_import_json"].value)
            self.view_dialog("JSONからインポートしました")
        except Exception as ex:
            traceback.print_exception(ex)
            self.view_dialog(f"*** ERROR ***\nJSONからのインポートに失敗しました\n{ex}")

    def import_from_json(self, data_json: str) -> None:
        version: int = None
        try:
            data_dict = json.loads(data_json)
        except json.decoder.JSONDecodeError as ex:
            raise Exception("JSONフォーマットが不正です")

        if "version" in data_dict:
            try:
                version = int(data_dict["version"])
            except ValueError:
                pass

        if version is None or version > self._export_json_format_version:
            raise Exception(f"未知のJSONフォーマットVersionです\n入力されたフォーマットVersion:{version}")

        if "status" in data_dict:
            if "base_lv" in data_dict["status"]:
                self.dom_elements["base_lv"].value = data_dict["status"]["base_lv"]

            if "job_lv" in data_dict["status"]:
                self.dom_elements["job_lv"].value = data_dict["status"]["job_lv"]

            if "job_class" in data_dict["status"]:
                self.dom_elements["job_class"].value = data_dict["status"]["job_class"]

            for key in self._status_primary.keys():
                if key in data_dict["status"]:
                    self.dom_elements[key]["base"].value = data_dict["status"][key]

            for key in self._status_talent.keys():
                if key in data_dict["status"] and len(self.dom_elements[key]) > 0:
                    self.dom_elements[key]["base"].value = data_dict["status"][key]

        if "skills" in data_dict:
            pass

        if "equipments" in data_dict:
            pass

        if "additional_info" in data_dict:
            if "character_name" in data_dict["additional_info"]:
                self.dom_elements["input_character_name"].value = data_dict["additional_info"]["character_name"]

    def import_from_base64(self, data_base64: str) -> bool:
        success: bool = False
        try:
            data_compressed = binascii.a2b_base64(data_base64.encode("utf-8"))
            data_json = bz2.decompress(data_compressed)
            self.import_from_json(data_json.decode("utf-8"))
            success = True
        except Exception as ex:
            traceback.print_exception(ex)

        return success

    def export_to_json(self) -> str:
        data_json: dict[str] = {
            "version" : self._export_json_format_version,
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

        for key in self._status_primary.keys():
            value: int = 0
            try:
                value = int(self.dom_elements[key]["base"].value)
            except ValueError:
                pass

            data_json["status"][key] = value

        for key in self._status_talent:
            if key in self.dom_elements and len(self.dom_elements[key]) > 0:
                value: int = 0
                try:
                    value = int(self.dom_elements[key]["base"].value)
                except ValueError:
                    pass

                if value > 0:
                    data_json["status"][key] = value

        # dict => json
        data_json = json.dumps(data_json, ensure_ascii=False, indent=4)

        self.dom_elements["textarea_import_json"].value = data_json

        return data_json

    def export_to_base64(self) -> None:
        data_json: str = self.export_to_json()

        # json => bz2 copressed
        data_compressed = bz2.compress(data_json.encode("utf-8"), compresslevel=9)

        # bz2 compressed => base64
        data_base64 = binascii.b2a_base64(data_compressed).decode("utf-8")

        export_url = document.getElementById("export_url")
        url = self._prefix_url + self._suffix_url + "?" + data_base64
        export_url.href = url

    def calculation(self, event = None) -> None:
        if self._initialized != True:
            # initialize未完了の場合終了
            return

        success: bool = True
        print("[TRACE]", "Call def calculation")

        try:
            # calculation
            package.module_v1.pre_calc(self._prefix_url, self.dom_elements, self.load_datas)

        except Exception as ex:
            success = False
            traceback.print_exception(ex)

        if success == True:
            self.export_to_base64()

    def onclick_draw_status_window(self, event = None):
        self.calculation()
        self.draw_img_status_window()

    def draw_img_status_window(self, img_src: str = "./assets/statwin_bg.png"):
        img = Image.open(img_src)
        font_lg = ImageFont.truetype("./assets/SourceHanCodeJP-Medium.otf", size=10)
        font_md = ImageFont.truetype("./assets/SourceHanCodeJP-Medium.otf", size=9)
        font_logo = ImageFont.truetype("./assets/Melete-Regular.otf", size=11)
        draw = ImageDraw.Draw(img)

        draw.text((0,220), "Powerd by RODB", "#16507b", font=font_logo, align="left")

        draw.text((20,1), "基本情報", "#000000", font=font_lg, align="left")
        draw.text((236,1), "ステータス", "#000000", font=font_lg, align="left")
        draw.text((236,122), "特性ステータス", "#000000", font=font_lg, align="left")

        character_name: str = self.dom_elements["input_character_name"].value
        draw.text((10,20), character_name, "#000000", font=font_lg, align="left")
        draw.text((10,36), str(self.dom_elements["job_class"].value).capitalize(), "#000000", font=font_md, align="left")

        draw.text((16,50), "HP", "#000000", font=font_md, align="left")
        hp_max = self.dom_elements["hp_max"].value
        draw.text((100,58), f"{hp_max} / {hp_max}", "#000000", font=font_md, align="center", anchor="mm")

        draw.text((16,66), "SP", "#000000", font=font_md, align="left")
        sp_max = self.dom_elements["sp_max"].value
        draw.text((100,72), f"{sp_max} / {sp_max}", "#000000", font=font_md, align="center", anchor="mm")

        draw.text((16,100), "Base Lv. " + self.dom_elements["base_lv"].value, "#000000", font=font_md, align="left")
        draw.text((16,112), "Job Lv. " + self.dom_elements["job_lv"].value, "#000000", font=font_md, align="left")

        weight_max: str = self.dom_elements["weight_max"].value
        zeny: int = 999999999
        draw.text((216,136), f"Weight:0/{weight_max} Zeny:{zeny:,d}", "#000000", font=font_md, align="right", anchor="rt")

        for key in self._status_primary.keys():
            text = self.dom_elements[key]["base"].value
            text += "+"
            text += self.dom_elements[key]["bonus"].value
            position = self._status_primary[key]["status_window_position"]
            draw.text(position, text, "#000000", font=font_md, align="left")

        for key in self._status_talent.keys():
            text = self.dom_elements[key]["base"].value
            text += "+"
            text += self.dom_elements[key]["bonus"].value
            position = self._status_talent[key]["status_window_position"]
            draw.text(position, text, "#000000", font=font_md, align="left")

        for key in self._status_result.keys():
            if "status_window_position" in self._status_result[key]:
                text: str = ""
                if key in  ("atk", "def", "matk", "mdef"):
                    text = self.dom_elements[key]["base"].value
                    text += " + "
                    text += self.dom_elements[key]["bonus"].value
                elif key == "flee":
                    text = self.dom_elements[key].value
                    text += " + "
                    text += "{:.0f}".format(float(self.dom_elements["complete_avoidance"].value))
                elif key in ("critical", "aspd"):
                    text = "{:.0f}".format(float(self.dom_elements[key].value))
                else:
                    text = self.dom_elements[key].value

                position = self._status_result[key]["status_window_position"]
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

        daialog = document.getElementById("daialog")
        daialog.showModal()

    def close_dialog(self, event = None) -> None:
        daialog = document.getElementById("daialog")
        daialog.close()

def main():
    query_strings = URLSearchParams.new(location.search)

    instance = Simulator("https://rodb.aws.0nyx.net/simulator/", "v1.html")

    result_import: bool = None
    if str(query_strings) != "":
        data = str(query_strings)
        data_base64 = urllib.parse.unquote(data)
        result_import = instance.import_from_base64(data_base64)

    if result_import is not None:
        if result_import == True:
            instance.view_dialog("インポートが完了しました")
        else:
            instance.view_dialog("*** ERROR ***\nインポートが失敗しました")
            return

    instance.calculation()
    instance.draw_img_status_window()

if __name__ == "__main__":
    main()
