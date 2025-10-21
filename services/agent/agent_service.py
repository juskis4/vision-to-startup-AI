from services.llm.base import LLM
from services.database.base import Database
from typing import Optional
import time
from schemas.idea import IdeaSchema, IcpSchema, RedditSchema, ResponseSchema, RedditFeedback


class AgentService:
    def __init__(self, llm: LLM, db: Database):
        self.llm = llm
        self.db = db

    async def handle_user_message(self,
                                  user_input: str,
                                  user_id: str,
                                  options: Optional[dict] = None) -> ResponseSchema:

        # DUMMY RESPONSE - Simulate 1 minute processing time for frontend testing
        print(f"[DUMMY MODE] Simulating idea generation for: {user_input}")
        time.sleep(60)  # Simulate 1 minute processing time

        # Create dummy idea schema
        idea = IdeaSchema(
            title="AI-Powered Smart Productivity Assistant",
            description="An intelligent personal assistant that learns your work patterns and automatically optimizes your daily schedule, prioritizes tasks, and eliminates time-wasting activities.",
            problem_statement="Busy professionals struggle to manage their time effectively, leading to decreased productivity and increased stress levels.",
            key_features=[
                "Intelligent task prioritization based on deadlines and importance",
                "Automatic calendar optimization and meeting scheduling",
                "Real-time productivity tracking and insights",
                "Smart notification management to reduce distractions",
                "Integration with popular productivity and communication tools"
            ],
            confidence=0.85
        )

        # Create dummy ICP schema
        icp = IcpSchema(
            target_demographics=[
                "Busy professionals aged 25-45",
                "Remote workers and freelancers",
                "Small business owners",
                "Project managers and team leads"
            ],
            ideal_customer_profile="Mid-level to senior professionals earning $50k-$150k annually, primarily in tech, consulting, and creative industries. They value efficiency and are willing to pay for tools that save time and reduce stress.",
            pain_points=[
                "Constant context switching between tasks and tools",
                "Difficulty prioritizing work when everything seems urgent",
                "Spending too much time in unproductive meetings",
                "Forgetting important tasks and deadlines",
                "Feeling overwhelmed by information overload"
            ],
            user_motivations=[
                "Achieve better work-life balance",
                "Increase productivity and career advancement",
                "Reduce stress and mental load",
                "Gain more time for meaningful work",
                "Stay organized and in control"
            ],
            confidence=0.82
        )

        # Create dummy Reddit analysis schema
        reddit = RedditSchema(
            supportive_feedback=[
                RedditFeedback(
                    comment="I've been looking for something like this for years! My calendar is a disaster and I can never find time for the important stuff.",
                    username="u/busyprofessional2024",
                    subreddit="r/productivity",
                    link="https://www.reddit.com/r/productivity/comments/dummy1"
                ),
                RedditFeedback(
                    comment="As a project manager, this would be a game changer. I spend half my day just figuring out what to work on next.",
                    username="u/projectmanager_jane",
                    subreddit="r/ProjectManagement",
                    link="https://www.reddit.com/r/ProjectManagement/comments/dummy2"
                ),
                RedditFeedback(
                    comment="The meeting optimization feature alone would save me hours each week. Take my money!",
                    username="u/meetinghater",
                    subreddit="r/antiwork",
                    link="https://www.reddit.com/r/antiwork/comments/dummy3"
                )
            ],
            challenging_feedback=[
                RedditFeedback(
                    comment="Another productivity app? There are already dozens of these. What makes this different from Notion or Todoist?",
                    username="u/skeptical_user",
                    subreddit="r/productivity",
                    link="https://www.reddit.com/r/productivity/comments/dummy4"
                ),
                RedditFeedback(
                    comment="I tried similar apps before and they just became another thing to manage. How do you avoid feature bloat?",
                    username="u/minimalist_mike",
                    subreddit="r/minimalism",
                    link="https://www.reddit.com/r/minimalism/comments/dummy5"
                )
            ],
            relevant_subreddits=[
                "r/productivity",
                "r/GetMotivated",
                "r/projectmanagement",
                "r/entrepreneur",
                "r/remotework",
                "r/freelance",
                "r/consulting",
                "r/timemanagement"
            ],
            confidence=0.78
        )

        response_schema = ResponseSchema(
            idea=idea,
            icp=icp,
            reddit_analysis=reddit
        )

        try:
            self.db.insert_plan(
                user_id=user_id,
                idea=user_input,
                response=response_schema.model_dump()
            )
            print(
                f"[DUMMY MODE] Saved dummy response to database for user {user_id}")
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

    async def generate_script(self, idea_data: dict, service_type: str, options: Optional[dict] = None) -> dict:
        # TODO: Replace with actual LLM call when ready
        import asyncio
        await asyncio.sleep(25)

        dummy_script = f"""
        # Website Development Prompt for {service_type}
        
        ## Project Overview
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        
        ## Technical Specifications
        
        ### Database Schema
        ```sql
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE projects (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(50) DEFAULT 'draft'
        );
        ```
        
        ### API Endpoints
        - GET /api/users - Retrieve user information
        - POST /api/auth/login - User authentication
        - GET /api/projects - List user projects
        - POST /api/projects - Create new project
        
        ### Frontend Components
        1. **Header Component** - Navigation and user menu
        2. **Dashboard** - Main user interface
        3. **Project List** - Display user projects
        4. **Project Form** - Create/edit projects
        
        ## Implementation Details
        
        ### Technology Stack
        - Frontend: React.js with TypeScript
        - Backend: Node.js with Express
        - Database: PostgreSQL
        - Authentication: JWT tokens
        - Styling: Tailwind CSS
        
        ### File Structure
        ```
        /src
            /components
            Header.tsx
            Dashboard.tsx
            ProjectList.tsx
            /pages
            Login.tsx
            Home.tsx
            /services
            api.ts
            auth.ts
        ```
        
        ### Key Features
        - User registration and authentication
        - Project creation and management
        - Real-time updates
        - Responsive design
        - Data validation and error handling
        
        ## User Experience
        
        ### User Journey
        1. Landing page with clear value proposition
        2. Simple registration/login process
        3. Intuitive dashboard layout
        4. Easy project creation workflow
        
        ### Design Principles
        - Clean, modern interface
        - Consistent color scheme and typography
        - Mobile-first responsive design
        - Accessibility compliance (WCAG 2.1)
        
        ## Security Considerations
        - Password hashing with bcrypt
        - JWT token expiration
        - HTTPS enforcement
        - Input validation and sanitization
        - CORS configuration
        
        Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
        """

        print(
            f"Script generation complete (dummy mode), Service: {service_type}")

        return {
            "script": dummy_script.strip(),
            "confidence": 0.85,  # Dummy confidence score
            "service_type": service_type
        }
