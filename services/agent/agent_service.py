from services.llm.base import LLM
from services.database.base import Database
from typing import Optional
from schemas.idea import IdeaSchema, IcpSchema, RedditSchema, ResponseSchema


class AgentService:
    def __init__(self, llm: LLM, db: Database):
        self.llm = llm
        self.db = db

    async def handle_user_message(self,
                                  user_input: str,
                                  user_id: str,
                                  options: Optional[dict] = None) -> ResponseSchema:

        idea = await self.extract_info(user_input=user_input, options=options)
        if idea.confidence < 0.7:
            print(f"Low confidence score: {idea.confidence}")
            return None

        icp = await self.extract_icp(context=idea.model_dump_json(), options=options)
        if icp.confidence < 0.7:
            print(f"Low confidence score: {icp.confidence}")
            return None

        reddit = await self.extract_reddit(
            context=f"{idea.model_dump_json()}\n\n{icp.model_dump_json()}",
            options=options
        )
        if reddit.confidence < 0.7:
            print(f"Low confidence score: {reddit.confidence}")
            return None

        response_schema = ResponseSchema(
            idea=idea, icp=icp, reddit_analysis=reddit
        )

        try:
            self.db.insert_plan(
                user_id=user_id,
                idea=user_input,
                response=response_schema.model_dump()
            )
        except Exception as e:
            print(f"Failed to save to database: {str(e)}")

        return response_schema

    async def extract_info(self, user_input: str, options: Optional[dict] = None) -> IdeaSchema:
        print("Starting info extraction analysis")

        response = await self.llm.generate_parse(
            user_input=user_input,
            system=f"""
            You are an experienced founder and market researcher. You need to validate an idea and improve it. The goal is to make sure that the idea is solving a real, painful problem and has a clear, feasible path to build and launch. Deconstruct idea backwards to identify the core problem it solves. Answer questions like: “What result does this app create?”, “What\’s hard or frustrating about achieving that result today?”, “Why would someone pay for this?”\n
            Input: a short textual idea for an app or a business.\n"
            Rules:\n"
            - Keep description short (3-4 sentences).\n
            """,
            options=options,
            schema=IdeaSchema
        )

        print(
            f"Extraction complete, Confidence: {response.confidence:.2f}")
        return response

    async def extract_icp(self, context: str, options: Optional[dict] = None) -> IcpSchema:
        print("Starting ICP analysis")

        response = await self.llm.generate_parse(
            user_input=context,
            system=f"""
            You are an experienced founder and market researcher. Create a detailed Ideal Customer Profile (ICP) that includes: Demographics (age, location, occupation), Psychographics (values, beliefs, goals), Pain points related to the problem. Find patterns.\n
            Input: Business or app idea, with a description, core problem and main functionality.\n"
            """,
            options=options,
            schema=IcpSchema
        )

        print(
            f"Extraction complete, Confidence: {response.confidence:.2f}")
        return response

    async def extract_reddit(self, context: str, options: Optional[dict] = None) -> RedditSchema:
        print("Starting Reddit analysis")

        response = await self.llm.generate_parse(
            user_input=context,
            system=f"""
            You output ONLY JSON that validates against RedditSchema. No markdown, no prose.

            Rules for fields:
            - observations[*].quote: <= 180 chars, replace any double quotes (") with single quotes (') OR escape them.
            - No newlines in strings. No trailing commas. Strict JSON.

            Based on the ICP, identify 3 relevant subreddits where they hang out. Find top upvoted posts related to the problem and analyze their content. Use sentiment analysis or pattern detection to determine if people are frustrated, desperate, or actively seeking solutions. Summarize what you find to help validate if this is a painkiller, not a vitamin.\n
            Input: Business or app idea, with a description, core problem, main functionality and ideal customer profile (ICP).\n"
            """,
            options=options,
            schema=RedditSchema,
            web_search=True
        )

        print(
            f"Extraction complete, Confidence: {response.confidence:.2f}")
        return response
