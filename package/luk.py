import os

__filename__ = os.path.splitext(os.path.basename(__file__))[0]

def calc(dom_elements: dict):
    point_bonus: int = 0
    point_baisc: int  = int(dom_elements[__filename__]["basic"].value)

    dom_elements[__filename__]["bonus"].value = point_bonus
