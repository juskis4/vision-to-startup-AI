from services.llm.base import LLM
from services.database.base import Database
from typing import Optional
from schemas.idea import IdeaSchema


class AgentService:
    def __init__(self, llm: LLM, db: Database):
        self.llm = llm
        self.db = db

    async def handle_user_message(self,
                                  user_input: str,
                                  user_id: str,
                                  options: Optional[dict] = None) -> None:

        eventInfo = await self.extract_info(
            user_input=user_input,
            options=options
        )

        if eventInfo.confidence < 0.7:
            print(f"Low confidence score: {eventInfo.confidence}")
            return None

        try:
            self.db.insert_plan(
                user_id=user_id,
                idea=user_input,
                response=eventInfo.model_dump_json()
            )
        except Exception as e:
            print(f"Failed to save to database: {str(e)}")

        return eventInfo

    async def extract_info(self, user_input: str, options: Optional[dict] = None) -> IdeaSchema:
        print("Starting info extraction analysis")

        response = await self.llm.generate_parse(
            user_input=user_input,
            system=f"""
            You are an experienced product manager and investor.\n
            Input: a short textual idea for an app or a business.\n"
            Rules:\n"
            - Keep description short (1-3 sentences).\n
            - Provide 4-8 functionality bullets, ordered by importance.\n
            - Provide 3-6 pros and 3-6 cons.\n
            - Suggested next steps should be practical and ordered.\n
            """,
            options=options,
            schema=IdeaSchema
        )

        print(
            f"Extraction complete, Confidence: {response.confidence:.2f}")
        return response
