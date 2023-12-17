import math

import requests
from pyscript import document

data_table: dict = {
    "job_class": None,
    "hp": None,
    "sp": None,
    "weapon_type": None
}

def pre_calc(prefix_url: str, dom_elements: dict[str], load_datas: dict[str]) -> dict:
    point: dict = {
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

    headers={
        "Content-Type": "application/json",
        "Accept-Encoding": None, # delete unsafe header
        "Connection": None # delete unsafe haader
    }

    # 職業
    job_class: str = str(dom_elements["job_class"].value).replace(" ", "_")
    job_class_id: int = None
    parent_direcoty: str = ""
    if "job_classes" in load_datas:
        job_class_ids = [key for key, value in load_datas["job_classes"].items() if value["class"] == job_class]
        if len(job_class_ids) > 0:
            job_class_id = job_class_ids[0]
            if  "parent_directory" in load_datas["job_classes"][job_class_id]:
                parent_direcoty = load_datas["job_classes"][job_class_id]["parent_directory"] + "/"

    if job_class_id is None:
        # 正しいjobが選択されてない場合はreturn
        return

    # load HP table
    if data_table["hp"] is None or data_table["job_class"] != job_class:
        response = requests.get(prefix_url + f"data/jobs/{parent_direcoty}{job_class}/hp.json", headers=headers)
        if response.status_code == 200:
            data_table["hp"] = response.json()
        else:
            data_table["hp"] = {}

    # load SP table
    if data_table["sp"] is None or data_table["job_class"] != job_class:
        response = requests.get(prefix_url + f"data/jobs/{parent_direcoty}{job_class}/sp.json", headers=headers)
        if response.status_code == 200:
            data_table["sp"] = response.json()
        else:
            data_table["sp"] = {}

    # load weapon type table
    if data_table["weapon_type"] is None or data_table["job_class"] != job_class:
        response = requests.get(prefix_url + f"data/jobs/{parent_direcoty}{job_class}/weapon_type.json", headers=headers)
        if response.status_code == 200:
            data_table["weapon_type"] = response.json()
        else:
            data_table["weapon_type"] = {}

        # Right : Main weapon type
        child_nodes = dom_elements["select_weapon_type_right"].childNodes
        for node in child_nodes:
            dom_elements["select_weapon_type_right"].removeChild(node)

        if data_table["weapon_type"] is not None and "right" in data_table["weapon_type"]:
            for key in data_table["weapon_type"]["right"]:
                data = data_table["weapon_type"]["right"][key]
                child_class = document.createElement("option")
                child_class.value = key
                if "display_name" in data:
                    child_class.label = data["display_name"]

                dom_elements["select_weapon_type_right"].appendChild(child_class)

        # Left : Sub weapon type
        child_nodes = dom_elements["select_weapon_type_left"].childNodes
        for node in child_nodes:
            dom_elements["select_weapon_type_left"].removeChild(node)

        if data_table["weapon_type"] is not None and "left" in data_table["weapon_type"]:
            if len(data_table["weapon_type"]["left"]) == 0:
                dom_elements["select_weapon_type_left"].disabled = True
            else:
                dom_elements["select_weapon_type_left"].disabled = False

            for key in data_table["weapon_type"]["left"]:
                data = data_table["weapon_type"]["left"][key]
                child_class = document.createElement("option")
                child_class.value = key
                if "display_name" in data:
                    child_class.label = data["display_name"]

                dom_elements["select_weapon_type_left"].appendChild(child_class)

    # 読み込んだtableのjob_classを記録しておく
    data_table["job_class"] = job_class

    # Max HP
    hp_base_point: int = 0
    if "additional_info" in load_datas and "hp_base_point" in load_datas["additional_info"]:
        hp_base_point = load_datas["additional_info"]["hp_base_point"]
    else:
        hp_base_point = int(data_table["hp"][str(point["base_lv"])])
    status_hp_max = str(int(hp_base_point + (hp_base_point * (point["vit"] + point["vit_bonus"]) / 100)))
    dom_elements["hp_max"].value = status_hp_max

    # HP Recovery

    # Max SP
    sp_base_point: int = 0
    if "additional_info" in load_datas and "sp_base_point" in load_datas["additional_info"]:
        sp_base_point = load_datas["additional_info"]["sp_base_point"]
    else:
        sp_base_point = int(data_table["sp"][str(point["base_lv"])])
    status_sp_max = str(int(sp_base_point + (sp_base_point * (point["int"] + point["int_bonus"]) / 100)))
    dom_elements["sp_max"].value = status_sp_max

    # SP Recovery

    # Atk(not bow)
    status_atk = str(int((point["str"] + point["str_bonus"])
            + (point["dex"] + point["dex_bonus"]) * 0.2
            + (point["luk"] + point["luk_bonus"]) * 0.3
            ))
    dom_elements["atk"]["base"].value = status_atk

    # Def
    status_def_base = str(int(point["base_lv"] * 0.5
                            + (point["agi"] + point["agi_bonus"]) * 0.2
                            + (point["vit"] + point["vit_bonus"]) * 0.5
                            ))
    dom_elements["def"]["base"].value = status_def_base

    # Matk
    status_matk_base = str(int((point["int"] + point["int_bonus"])
                            + (point["dex"] + point["dex_bonus"]) * 0.2
                            + (point["luk"] + point["luk_bonus"]) * 0.3
                            ))
    dom_elements["matk"]["base"].value = status_matk_base

    # Mdef
    status_mdef_base = str(int(point["base_lv"] * 0.2
                            + (point["int"] + point["int_bonus"])
                            + (point["vit"] + point["vit_bonus"]) * 0.2
                            + (point["dex"] + point["dex_bonus"]) * 0.2
                            ))
    dom_elements["mdef"]["base"].value = status_mdef_base

    # Hit
    status_hit = str(int(175 + point["base_lv"]
                        + (point["dex"] + point["dex_bonus"])
                        + (point["luk"] + point["luk_bonus"]) * 0.3
                        ))
    dom_elements["hit"].value = status_hit

    # Flee
    status_flee = str(int(100 + point["base_lv"]
                        + (point["agi"] + point["agi_bonus"])
                        + (point["luk"] + point["luk_bonus"]) * 0.2
                        ))
    dom_elements["flee"].value = status_flee

    # 完全回避 : Complete avoidance
    status_complete_avoidance = str(1+ int(((point["luk"] + point["luk_bonus"]) *0.1)*10)/10)
    dom_elements["complete_avoidance"].value = status_complete_avoidance

    # Critical
    status_critical = str(int((1 + ((point["luk"] + point["luk_bonus"]) *0.3))*10)/10)
    dom_elements["critical"].value = status_critical

    # Aspd(hand)
    aspd_base_point: int = 152
    aspd_penalty: float = (aspd_base_point - 144) / 50
    shield_correction_point: float = 0 #盾があれば-7～
    on_horseback_point: float = 1 #未騎乗
    #on_horseback_point: float = 0.5 + on_horseback_skill_lv * 0.1 #騎乗時
    status_aspd = str(int((aspd_base_point + (math.sqrt(((point["agi"] + point["agi_bonus"]) * 3027 / 300) + ((point["dex"] + point["dex_bonus"]) * 55 / 300)) * (1 - aspd_penalty)) + shield_correction_point) * on_horseback_point * 10)/10)
    dom_elements["aspd"].value = status_aspd
