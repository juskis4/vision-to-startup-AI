from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List


class Database(ABC):

    @abstractmethod
    def insert_plan(self, user_id: str, idea: str, response: Dict[str, Any], schema_version: int = 1) -> Any:
        raise NotImplementedError("insert_plan method must be implemented")

    @abstractmethod
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("get_plan method must be implemented")

    @abstractmethod
    def list_plans(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("list_plans method must be implemented")
