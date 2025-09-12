from .base import Database
from typing import List, Dict, Any, Optional
from supabase import create_client, Client


class SupabaseDB(Database):
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)

    def insert_plan(self, user_id: str, idea: str, response: Dict[str, Any], schema_version: int = 1) -> Any:
        data = {
            "user_id": user_id,
            "idea": idea,
            "response": response,
            "schema_version": schema_version,
        }
        result = self.client.table("business_plans").insert(data).execute()
        return result.data

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        result = self.client.table("business_plans").select(
            "*").eq("id", plan_id).execute()
        if result.data:
            return result.data[0]
        return None

    def list_plans(self) -> List[Dict[str, Any]]:
        result = self.client.table("business_plans").select(
            "*").order("created_at", desc=True).execute()
        return result.data
