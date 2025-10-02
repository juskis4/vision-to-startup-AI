from services.celery_app import celery_app
from services.redis_jobs import redis_job_manager
from services.database.supabase_db import SupabaseDB
from services.llm.openai_llm import OpenAILLM
from services.agent.agent_service import AgentService
from config.settings import settings


@celery_app.task(bind=True)
def generate_prompt_task(self, job_id: str):
    """
    Celery task to generate prompts for ideas
    """
    try:
        # Get job data
        job_data = redis_job_manager.get_job(job_id)
        if not job_data:
            print(f"Job {job_id} not found or expired")
            return

        if job_data["status"] in ["succeeded", "failed"]:
            print(
                f"Job {job_id} already completed with status: {job_data['status']}")
            return

        # Update status to running
        redis_job_manager.update_job(job_id, status="running", progress=0.05)

        # Initialize services
        db = SupabaseDB(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        llm = OpenAILLM(
            api_key=settings.OPENAI_API_KEY,
            model=settings.DEFAULT_MODEL,
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.DEFAULT_TEMPERATURE
        )
        agent = AgentService(llm=llm, db=db)

        # Get idea data
        idea_id = job_data["idea_id"]
        service_type = job_data["service_type"]

        # Validate idea exists
        idea_data = db.get_idea_by_id(idea_id)
        if not idea_data:
            redis_job_manager.update_job(
                job_id,
                status="failed",
                error=f"Idea with ID '{idea_id}' not found"
            )
            return

        # Update progress
        redis_job_manager.update_job(job_id, progress=0.2)

        # Generate the prompt using the existing agent service
        import asyncio
        script_result = asyncio.run(
            agent.generate_script(idea_data, service_type))

        # Update progress
        redis_job_manager.update_job(job_id, progress=0.8)

        if "error" in script_result:
            redis_job_manager.update_job(
                job_id,
                status="failed",
                error=f"Failed to generate prompt: {script_result['error']}"
            )
            return

        # Extract the generated content as a prompt
        # The script content will serve as our prompt
        prompt_content = script_result["script"]

        # Save to Supabase prompts table
        save_result = db.save_prompt(idea_id, service_type, prompt_content)

        if not save_result["success"]:
            redis_job_manager.update_job(
                job_id,
                status="failed",
                error=f"Failed to save prompt: {save_result['error']}"
            )
            return

        # Update job with success
        redis_job_manager.update_job(
            job_id,
            status="succeeded",
            progress=1.0,
            prompt_id=save_result["prompt_id"]
        )

        print(
            f"Successfully generated prompt for idea {idea_id}, service {service_type}")

    except Exception as e:
        print(f"Error in generate_prompt_task for job {job_id}: {str(e)}")
        redis_job_manager.update_job(
            job_id,
            status="failed",
            error=f"Internal error: {str(e)}"
        )
