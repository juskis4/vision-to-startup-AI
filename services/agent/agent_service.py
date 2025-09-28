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

        idea = await self.extract_idea(user_input=user_input, options=options)
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

    async def extract_idea(self, user_input: str, options: Optional[dict] = None) -> IdeaSchema:
        print("Starting info extraction analysis")

        response = await self.llm.generate_parse(
            user_input=user_input,
            system=f"""
            You are an experienced founder and market researcher. You need to validate an idea and improve it. The goal is to make sure that the idea is solving a real, painful problem and has a clear, feasible path to build and launch.

            Required outputs:
            - title: Catchy, concise title (max 100 chars)
            - description: Brief 1-3 sentence overview (max 500 chars)
            - problem_statement: Clear core problem definition (max 300 chars)
            - key_features: 3-7 main capabilities/features as bullet points
            - confidence: Quality score (0.0-1.0) - use as guard for response relevance

            Analysis approach:
            - Deconstruct idea backwards to identify the core problem it solves
            - Answer: "What result does this create?", "What's frustrating about achieving that today?", "Why would someone pay for this?"
            - Focus on pain points, not nice-to-haves
            - Ensure features directly address the core problem

            Be concise and focused. High confidence (0.8+) only for clear, validated problems with feasible solutions.
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
            You are an experienced founder and market researcher. Create a detailed Ideal Customer Profile (ICP) based on the provided business idea.

            Required outputs:
            - target_demographics: 3-6 demographic as tags (e.g., "Busy professionals aged 25-45", "Health-conscious individuals")
            - ideal_customer_profile: Detailed description of the ideal customer (max 400 chars) including demographics, income, location, and characteristics
            - pain_points: 3-7 specific pain points the target customers face
            - user_motivations: 3-7 key motivations that drive users to seek this solution
            - confidence: Quality score (0.0-1.0) - use as guard for response relevance

            Analysis approach:
            - Identify patterns in customer behavior and needs
            - Focus on specific, actionable demographic segments
            - Ensure pain points directly relate to the core problem
            - Make motivations clear and compelling
            - Be specific rather than generic

            High confidence (0.8+) only for well-defined, realistic customer profiles with clear pain points.
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
            You are an experienced market researcher analyzing Reddit for business validation. Output ONLY valid JSON matching RedditSchema.

            Required outputs:
            - supportive_feedback: 1-5 positive Reddit comments or posts with username (u/name), subreddit (r/name), comment text (max 300 chars), and link to the comment/post
            - challenging_feedback: 1-3 critical/negative Reddit comments with same structure
            - relevant_subreddits: 4-8 subreddit names for further research (format: r/SubredditName)
            - confidence: Quality score (0.0-1.0) - use as guard for response relevance

            Field validation rules:
            - username: Must match pattern "u/[username]" 
            - subreddit: Must match pattern "r/[subredditname]"
            - comment: Max 300 chars, replace quotes with single quotes
            - link: Valid Reddit URL to the comment/post
            - No newlines in strings, strict JSON format

            Analysis approach:
            - Find real Reddit discussions about the problem space
            - Categorize feedback as supportive (validates need) vs challenging (skeptical/critical)
            - Use sentiment analysis to determine if people are frustrated and seeking solutions
            - Validate this is a "painkiller" problem (urgent, essential need) vs "vitamin" (nice-to-have enhancement)
            - Look for evidence of: desperation, active seeking of alternatives, willingness to pay, time/money being wasted

            High confidence (0.8+) only for genuine, relevant Reddit discussions that clearly validate or challenge the business idea.
            """,
            options=options,
            schema=RedditSchema,
            web_search=True
        )

        print(
            f"Extraction complete, Confidence: {response.confidence:.2f}")
        return response
