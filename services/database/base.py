from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List


class Database(ABC):

    @abstractmethod
    def insert_plan(self, user_id: str, idea: str, response: Dict[str, Any], schema_version: int = 1) -> Any:
        raise NotImplementedError("insert_plan method must be implemented")

    @abstractmethod
    def get_all_ideas(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("get_all_ideas method must be implemented")

    @abstractmethod
    def get_idea_by_id(self, idea_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("get_idea_by_id method must be implemented")

    @abstractmethod
    def get_idea_summary_by_id(self, idea_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("get_idea_summary_by_id method must be implemented")

    @abstractmethod
    def update_idea_field(self, idea_id: str, field_name: str, field_value: str) -> Dict[str, Any]:
        raise NotImplementedError(
            "update_idea_field method must be implemented")

    @abstractmethod
    def update_idea_list(self, idea_id: str, list_type: str, items: List[str]) -> Dict[str, Any]:
        raise NotImplementedError(
            "update_idea_list method must be implemented")

    @abstractmethod
    def save_prompt(self, idea_id: str, service_type: str, prompt: str) -> Dict[str, Any]:
        raise NotImplementedError(
            "save_prompt method must be implemented")

    @abstractmethod
    def get_latest_prompt(self, idea_id: str, service_type: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError(
            "get_latest_prompt method must be implemented")

    @abstractmethod
    def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError(
            "get_prompt_by_id method must be implemented")

    @abstractmethod
    def get_prompts_metadata_by_idea_id(self, idea_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError(
            "get_prompts_metadata_by_idea_id method must be implemented")

    @abstractmethod
    def get_latest_prompt_for_idea_details(self, idea_id: str, service_type: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError(
            "get_latest_prompt_for_idea_details method must be implemented")
