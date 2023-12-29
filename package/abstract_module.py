from abc import ABC, abstractmethod

class AbstractCalculationModule(ABC):
    _valid: bool = False
    _prefix_url: str = "/"
    _dom_elements: dict[str] = {}
    _load_datas: dict[str] = {}
    _point: dict = {}
    _job_class_name: str = None
    _job_class_idx: int = None

    _headers={
        "Content-Type": "application/json",
        "Accept-Encoding": None, # delete unsafe header
        "Connection": None # delete unsafe haader
    }

    def is_valid(self) -> bool:
        return self._valid

    def get_job_class_name(self) -> str:
        return self._job_class_name

    def get_job_class_idx(self) -> int:
        return self._job_class_idx

    @abstractmethod
    def __init__(self, prefix_url: str, dom_elements: dict[str], load_datas: dict[str]) -> None:
        pass

    @abstractmethod
    def pre_calc(self) -> None:
        pass

    @abstractmethod
    def calculation(self) -> None:
        pass
