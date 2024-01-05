from abc import ABC, abstractmethod

class AbstractCalculationModule(ABC):
    _valid: bool = False
    prefix_url: str = "/"
    dom_elements: dict[str] = {}
    load_datas: dict[str] = {}
    job_class_name: str = None
    job_class_idx: int = None

    headers={
        "Content-Type": "application/json",
        "Accept-Encoding": None, # delete unsafe header
        "Connection": None # delete unsafe header
    }

    def is_valid(self) -> bool:
        return self._valid

    def get_job_class_name(self) -> str|None:
        return self.job_class_name

    def get_job_class_idx(self) -> int|None:
        return self.job_class_idx

    @abstractmethod
    def __init__(self, prefix_url: str, dom_elements: dict[str], load_datas: dict[str]) -> None:
        pass

    @abstractmethod
    def pre_calc(self) -> None:
        pass

    @abstractmethod
    def calculation(self) -> None:
        pass
