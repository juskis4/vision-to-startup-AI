import asyncio
from services.celery_app import celery_app
from services.redis_jobs import redis_job_manager
from services.database.supabase_db import SupabaseDB
from services.llm.openai_llm import OpenAILLM
from services.agent.agent_service import AgentService
from config.settings import settings


@celery_app.task(bind=True)
def generate_idea_task(self, job_id: str):
    """
    Celery task for generating ideas asynchronously
    """
    try:
        job_data = redis_job_manager.get_job(job_id)
        if not job_data:
            print(f"Job {job_id} not found or expired")
            return

        if job_data["status"] in ["succeeded", "failed"]:
            print(
                f"Job {job_id} already completed with status: {job_data['status']}")
            return

        redis_job_manager.update_job(job_id, status="running", progress=0.05)

        # Initialize services

        db = SupabaseDB(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        llm = OpenAILLM(api_key=settings.OPENAI_API_KEY)
        agent = AgentService(llm=llm, db=db)

        # Extract job parameters
        user_input = job_data["user_input"]
        user_id = job_data["user_id"]
        llm_options = {
            "model": settings.DEFAULT_MODEL,
            "temperature": settings.DEFAULT_TEMPERATURE,
            "max_tokens": settings.MAX_TOKENS
        }

        redis_job_manager.update_job(job_id, status="running", progress=0.1)

        # Process idea generation using agent service
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            redis_job_manager.update_job(
                job_id, status="running", progress=0.5)

            response_schema = loop.run_until_complete(
                agent.handle_user_message(
                    user_input=user_input,
                    user_id=user_id,
                    options=llm_options
                )
            )

            redis_job_manager.update_job(
                job_id, status="running", progress=0.9)

            if response_schema:
                # For async jobs, we need to get the idea ID from the database
                # The agent service inserts the data but doesn't return the ID
                # We'll use the response data as our result for now
                redis_job_manager.complete_job(job_id, {
                    "response": response_schema.model_dump(),
                    "message": "Idea generated successfully"
                })
                print(
                    f"Idea generation completed successfully for job {job_id}")
            else:
                redis_job_manager.fail_job(
                    job_id, "Low confidence scores - idea generation failed")

        finally:
            loop.close()

    except Exception as e:
        print(f"Error in idea generation task {job_id}: {str(e)}")
        redis_job_manager.fail_job(job_id, f"Internal error: {str(e)}")
