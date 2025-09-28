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

    def get_all_ideas(self) -> List[Dict[str, Any]]:
        result = self.client.table("business_plans").select(
            "id, user_id, response, created_at"
        ).order("created_at", desc=True).execute()

        ideas = []
        for plan in result.data:
            response = plan.get("response", {})
            idea_data = response.get("idea", {}) if isinstance(
                response, dict) else {}
            icp_data = response.get("icp", {}) if isinstance(
                response, dict) else {}
            reddit_data = response.get("reddit_analysis", {}) if isinstance(
                response, dict) else {}

            idea_entry = {
                "id": plan["id"],
                "user_id": plan["user_id"],
                "created_at": plan["created_at"],
                "title": idea_data.get("title", ""),
                "description": idea_data.get("description", ""),
                "problem_statement": idea_data.get("problem_statement", ""),
                "target_demographics": icp_data.get("target_demographics", ""),
                "key_features_count": len(idea_data.get("key_features", [])),
                "reddit_insights_count": len(reddit_data.get("challenging_feedback", [])) + len(reddit_data.get("supportive_feedback", [])),
            }
            ideas.append(idea_entry)

        return ideas

    def get_idea_by_id(self, idea_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = self.client.table("business_plans").select(
                "id, user_id, idea, response, created_at, schema_version"
            ).eq("id", idea_id).execute()

            if not result.data or len(result.data) == 0:
                return None

        except Exception:
            return None

        plan = result.data[0]
        response = plan.get("response", {})

        idea_data = response.get("idea", {}) if isinstance(
            response, dict) else {}
        icp_data = response.get("icp", {}) if isinstance(
            response, dict) else {}
        reddit_data = response.get(
            "reddit_analysis", {}) if isinstance(response, dict) else {}

        return {
            "id": plan["id"],
            "user_id": plan["user_id"],
            "original_idea": plan["idea"],
            "created_at": plan["created_at"],
            "schema_version": plan.get("schema_version", 1),
            "idea": {
                "title": idea_data.get("title", ""),
                "description": idea_data.get("description", ""),
                "problem_statement": idea_data.get("problem_statement", ""),
                "key_features": idea_data.get("key_features", []),
                "confidence": idea_data.get("confidence", 0.0)
            },
            "icp": {
                "target_demographics": icp_data.get("target_demographics", []),
                "ideal_customer_profile": icp_data.get("ideal_customer_profile", ""),
                "pain_points": icp_data.get("pain_points", []),
                "user_motivations": icp_data.get("user_motivations", []),
                "confidence": icp_data.get("confidence", 0.0)
            },
            "reddit_analysis": {
                "supportive_feedback": reddit_data.get("supportive_feedback", []),
                "challenging_feedback": reddit_data.get("challenging_feedback", []),
                "relevant_subreddits": reddit_data.get("relevant_subreddits", []),
                "confidence": reddit_data.get("confidence", 0.0)
            }
        }
