# app.py
import base64
import binascii
import bz2
from io import BytesIO
import json
import traceback
import urllib.parse
from pyscript import document
from js import location,URLSearchParams
from PIL import Image, ImageFont, ImageDraw
import requests
import pyodide_http
pyodide_http.patch_all()

import package


class Simulator:
    _initialized: bool = False
    _export_json_format_version: int = 1
    _prefix_url: str = "/"
    _suffix_url: str = "index.html"

    dom_elements: dict[str] = {}
    load_datas: dict[str] = {}

    _status_bases: dict = {
        "str": {
            "status_window_position" : (36, 6)
        },
        "agi": {
            "status_window_position" : (36, 22)
        },
        "vit": {
            "status_window_position" : (36, 38)
        },
        "int": {
            "status_window_position" : (36, 54)
        },
        "dex": {
            "status_window_position" : (36, 70)
        },
        "luk": {
            "status_window_position" : (36, 86)
        }
    }
    _status_specials: dict = {
        "pow": {
            "status_window_position" : (36, 128)
        },
        "sta": {
            "status_window_position" : (36, 144)
        },
        "wis": {
            "status_window_position" : (36, 160)
        },
        "spl": {
            "status_window_position" : (36, 176)
        },
        "con": {
            "status_window_position" : (36, 192)
        },
        "crt": {
            "status_window_position" : (36, 208)
        }
    }

    _status_result: dict = {
        "hp_max": {
            "status_window_position" : (0, 0)
        },
        "hp_recovery": {
        },
        "sp_max": {
            "status_window_position" : (0, 0)
        },
        "sp_recovery": {
        },
        "hit": {
            "status_window_position" : (0, 0)
        },
        "flee": {
            "status_window_position" : (0, 0)
        },
        "complete_avoidance": {
            "status_window_position" : (0, 0)
        },
        "critical": {
            "status_window_position" : (0, 0)
        },
        "aspd": {
            "status_window_position" : (0, 0)
        }
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

        for key in self._status_bases.keys():
            self.dom_elements[key]: dict = {
                "base"  : document.getElementById(f"status_{key}_base"),
                "bonus" : document.getElementById(f"status_{key}_bonus"),
            }
            self.dom_elements[key]["base"].oninput = self.calculation

        # 特性ステータス
        for key in self._status_specials.keys():
            self.dom_elements[key]: dict = {
                "base"  : document.getElementById(f"status_{key}_base"),
                "bonus" : document.getElementById(f"status_{key}_bonus"),
            }
            self.dom_elements[key]["base"].oninput = self.calculation

        for key in ("atk", "def", "matk", "mdef"):
            self.dom_elements[key]: dict = {
                "base"  : document.getElementById(f"status_{key}_base"),
                "bonus" : document.getElementById(f"status_{key}_bonus"),
            }

        for key in self._status_result.keys():
            self.dom_elements[key] = document.getElementById(f"status_{key}")

        self.dom_elements["button_import_json"] = document.getElementById("button_import_json")
        self.dom_elements["button_import_json"].onclick = self.onclick_import_from_json

        self.dom_elements["textarea_import_json"] = document.getElementById("textarea_import_json")

        self.dom_elements["daialog_button_close"] = document.getElementById("daialog_button_close")
        self.dom_elements["daialog_button_close"].onclick = self.close_dialog

        self.dom_elements["img_status_window"] = document.getElementById("img_status_window")

        self.dom_elements["button_draw_status_window"] = document.getElementById("button_draw_status_window")
        self.dom_elements["button_draw_status_window"].onclick = self.onclick_draw_status_window

        response = requests.get(prefix_url + "data/job_classes.json")
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


        response = requests.get(prefix_url + "data/weapon_types.json")
        self.load_datas["weapon_types"] = response.json()

        if len(self.load_datas["weapon_types"]) > 0:
            # Right : Main weapon type
            self.dom_elements["select_weapon_type_right"] = document.getElementById("select_weapon_type_right")
            for idx in self.load_datas["weapon_types"]:
                child_class = document.createElement("option")
                data = self.load_datas["weapon_types"][idx]

                child_class.value = data["name"]
                if "display_name" in data:
                    child_class.label = data["display_name"]

                self.dom_elements["select_weapon_type_right"].appendChild(child_class)

            # Left : Sub weapon type
            self.dom_elements["select_weapon_type_left"]  = document.getElementById("select_weapon_type_left")
            for idx in self.load_datas["weapon_types"]:
                child_class = document.createElement("option")
                data = self.load_datas["weapon_types"][idx]

                if "allow_left" in data:
                    child_class.value = data["name"]
                    if "display_name" in data:
                        child_class.label = data["display_name"]
                    self.dom_elements["select_weapon_type_left"].appendChild(child_class)


        # initilzed finish
        self._initialized = True

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

            if "job_class_id" in data_dict["status"]:
                self.dom_elements["job_class"].value = self.load_datas["job_classes"][str(data_dict["status"]["job_class_id"])]["class"]

            for key in self._status_bases.keys():
                if key in data_dict["status"]:
                    self.dom_elements[key]["base"].value = data_dict["status"][key]

            for key in self._status_specials.keys():
                if key in data_dict["status"] and len(self.dom_elements[key]) > 0:
                    self.dom_elements[key]["base"].value = data_dict["status"][key]

        if "skills" in data_dict:
            pass

        if "equipments" in data_dict:
            pass

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

    def export_to_base64(self) -> None:
        data_json: dict[str] = {
            "version" : self._export_json_format_version,
            "status" : {
                "base_lv" : int(self.dom_elements["base_lv"].value),
                "job_lv" : int(self.dom_elements["job_lv"].value),
                "job_class_id": 0
            },
            "skills": {

            },
            "equipments": {

            },
            "items": {

            },
            "supports": {

            }
        }

        for key in self._status_bases.keys():
            value: int = 0
            try:
                value = int(self.dom_elements[key]["base"].value)
            except ValueError:
                pass

            data_json["status"][key] = value

        for key in self._status_specials:
            if key in self.dom_elements and len(self.dom_elements[key]) > 0:
                value: int = 0
                try:
                    value = int(self.dom_elements[key]["base"].value)
                except ValueError:
                    pass

                if value > 0:
                    data_json["status"][key] = value

        job_class = self.dom_elements["job_class"].value
        if job_class is not None and job_class != "":
            job_class_ids = [key for key, value in self.load_datas["job_classes"].items() if value["class"] == job_class]
            if len(job_class_ids) > 0:
                data_json["status"]["job_class_id"] = int(job_class_ids[0])

        # dict => json
        data_json = json.dumps(data_json, indent=4)
        self.dom_elements["textarea_import_json"].value = data_json

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
        self.draw_img_status_window()

    def draw_img_status_window(self, img_src: str = "./assets/statwin_bg.bmp"):
        img = Image.open(img_src)
        font = ImageFont.truetype("./assets/SourceCodePro-Regular.ttf", 10, 0)
        draw = ImageDraw.Draw(img)

        for key in self._status_bases.keys():
            text = self.dom_elements[key]["base"].value
            text += "+"
            text += self.dom_elements[key]["bonus"].value
            position = self._status_bases[key]["status_window_position"]
            draw.text(position, text, "#000000", font=font, align="left")

        for key in self._status_specials.keys():
            text = self.dom_elements[key]["base"].value
            text += "+"
            text += self.dom_elements[key]["bonus"].value
            position = self._status_specials[key]["status_window_position"]
            draw.text(position, text, "#000000", font=font, align="left")

        # zoom x2
        img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)

        buffer = BytesIO()
        img.save(buffer, "png")
        img_str = "data:image/bmp;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
        img_status_window = self.dom_elements["img_status_window"]
        img_status_window.src = img_str
        img_status_window.width = img.width
        img_status_window.height = img.height

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
