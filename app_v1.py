# app.py
import binascii
import bz2
import json
import traceback
from js import document,location,URLSearchParams
import urllib.parse

class Simulator:
    _initialized: bool = False
    _export_json_format_version: int = 1
    _prefix_url: str = "/"

    def __init__(self, prefix_url = "/") -> None:
        self._prefix_url = prefix_url

        self.status_lv_base = document.getElementById("status_lv_base")
        self.status_lv_base.oninput = self.calculation

        self.status_lv_job = document.getElementById("status_lv_job")
        self.status_lv_job.oninput = self.calculation

        self.status_str_basic = document.getElementById("status_str_basic")
        self.status_str_basic.oninput = self.calculation

        self.status_agi_basic = document.getElementById("status_agi_basic")
        self.status_agi_basic.oninput = self.calculation

        self.status_vit_basic = document.getElementById("status_vit_basic")
        self.status_vit_basic.oninput = self.calculation

        self.status_int_basic = document.getElementById("status_int_basic")
        self.status_int_basic.oninput = self.calculation

        self.status_dex_basic = document.getElementById("status_dex_basic")
        self.status_dex_basic.oninput = self.calculation

        self.status_luk_basic = document.getElementById("status_luk_basic")
        self.status_luk_basic.oninput = self.calculation

        button_import_json = document.getElementById("button_import_json")
        button_import_json.onclick = self.onclick_import_from_json

        self.export_json = document.getElementById("export_json")

        daialog_button_close = document.getElementById("daialog_button_close")
        daialog_button_close.onclick = self.close_dialog

        # initilzed finish
        self._initialized = True

    def onclick_import_from_json(self, event = None) -> None:
        try:
            self.import_from_json(self.export_json.value)
            self.export_to_base64() #base64にも反映
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
                self.status_lv_base.value = data_dict["status"]["base_lv"]

            if "job_lv" in data_dict["status"]:
                self.status_lv_job.value = data_dict["status"]["job_lv"]

            if "str" in data_dict["status"]:
                self.status_str_basic.value = data_dict["status"]["str"]

            if "agi" in data_dict["status"]:
                self.status_agi_basic.value = data_dict["status"]["agi"]

            if "vit" in data_dict["status"]:
                self.status_vit_basic.value = data_dict["status"]["vit"]

            if "int" in data_dict["status"]:
                self.status_int_basic.value = data_dict["status"]["int"]

            if "dex" in data_dict["status"]:
                self.status_dex_basic.value = data_dict["status"]["dex"]

            if "luk" in data_dict["status"]:
                self.status_luk_basic.value = data_dict["status"]["luk"]

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
        data_dict: dict[str] = {
            "version" : self._export_json_format_version,
            "status" : {
                "base_lv" : int(self.status_lv_base.value),
                "job_lv" : int(self.status_lv_job.value),
                "str" : int(self.status_str_basic.value),
                "agi" : int(self.status_agi_basic.value),
                "vit" : int(self.status_vit_basic.value),
                "int" : int(self.status_int_basic.value),
                "dex" : int(self.status_dex_basic.value),
                "luk" : int(self.status_luk_basic.value)
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

        # dict => json
        data_json = json.dumps(data_dict, indent=4)
        self.export_json.value = data_json

        # json => bz2 copressed
        data_compressed = bz2.compress(data_json.encode("utf-8"), compresslevel=9)

        # bz2 compressed => base64
        data_base64 = binascii.b2a_base64(data_compressed).decode("utf-8")

        export_url = document.getElementById("export_url")
        url = self._prefix_url + "?" + data_base64
        export_url.href = url

    def calculation(self, event = None) -> None:
        if self._initialized != True:
            # initialize未完了の場合終了
            return

        self.export_to_base64()

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

    instance = Simulator("https://rodb.aws.0nyx.net/simulator/v1.html")

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

    instance.export_to_base64()

if __name__ == "__main__":
    main()
