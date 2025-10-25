from fastapi import FastAPI, Request, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from services.messenger.telegram import TelegramMessenger
from services.llm.openai_llm import OpenAILLM
from services.database.supabase_db import SupabaseDB
from services.agent.agent_service import AgentService
from services.voice.openai_transcriber import OpenAITranscriber
from schemas.update import IdeaUpdateRequest, UpdateListRequest
from schemas.prompts import PromptGenerateResponse, JobStatusResponse, PromptResponse
from schemas.idea_generation import IdeaGenerateResponse, IdeaJobStatusResponse
from services.redis_jobs import redis_job_manager
from services.workers.prompt_worker import generate_prompt_task
from services.workers.idea_worker import generate_idea_task
import json

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processing_messages = set()

messenger = TelegramMessenger(token=settings.TELEGRAM_API_TOKEN)
llm = OpenAILLM(api_key=settings.OPENAI_API_KEY)
db = SupabaseDB(url=settings.SUPABASE_URL, key=settings.SUPABASE_KEY)
transcriber = OpenAITranscriber(
    api_key=settings.OPENAI_API_KEY, default_model=settings.TRANSCRIBE_MODEL)
agent_service = AgentService(llm=llm, db=db)


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    payload = await request.json()

    message_id = (payload.get("message") or payload.get(
        "callback_query", {}).get("message", {})).get("message_id")

    if message_id:
        if message_id in processing_messages:
            return {"ok": True}
        processing_messages.add(message_id)

    chat_id = str(payload.get("message", payload.get(
        "callback_query", {})).get("chat", {}).get("id"))

    try:
        msg = payload.get("message", {})

        if msg.get("text", {}):
            incoming_text = messenger.receive_message(payload)
        elif msg.get("voice", {}):
            audio_bytes = await messenger.download_voice(payload)
            incoming_text = await transcriber.transcribe(
                audio_bytes,
                language="en"
            )
        else:
            incoming_text = ""

        if not incoming_text:
            await messenger.send_message(chat_id, "Unsupported or empty message.")
            return {"ok": False}

        llm_options = {
            "model": settings.DEFAULT_MODEL,
            "temperature": settings.DEFAULT_TEMPERATURE,
            "max_tokens": settings.MAX_TOKENS
        }

        reply = await agent_service.handle_user_message(
            user_input=incoming_text,
            options=llm_options,
            user_id=chat_id
        )

        if reply:
            await messenger.send_message(chat_id, reply.model_dump_json())
        else:
            await messenger.send_message(chat_id, "Sorry, something went wrong.")

        return {"ok": True}

    except Exception as e:
        print(f"Error processing message: {str(e)}")
        await messenger.send_message(chat_id, "Sorry, an error occurred.")
        return {"ok": False}
    finally:
        if message_id and message_id in processing_messages:
            processing_messages.remove(message_id)
            print(
                f"Finished processing message {message_id}, removed from processing set")


@app.post("/ideas/generate", response_model=IdeaGenerateResponse)
async def generate_idea(
    user_input: str = Body(..., embed=True),
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    """
    Start async idea generation for web frontend
    """
    try:
        if not user_input or not user_input.strip():
            raise HTTPException(
                status_code=400,
                detail="User input is required"
            )

        user_id = "web_user"

        existing_job_id = redis_job_manager.get_dedupe_job_id(
            f"idea_generation_{user_id}", "idea", idempotency_key)

        if existing_job_id:
            job_data = redis_job_manager.get_job(existing_job_id)
            if job_data:
                return IdeaGenerateResponse(
                    job_id=existing_job_id,
                    status=job_data["status"],
                    poll_url=f"/idea-jobs/{existing_job_id}"
                )

        # Create new job
        job_id = redis_job_manager.create_job(
            f"idea_generation_{user_id}",
            "idea",
            idempotency_key,
            additional_data={
                "user_input": user_input.strip(),
                "user_id": user_id
            }
        )

        # Enqueue Celery task
        generate_idea_task.delay(job_id)

        return IdeaGenerateResponse(
            job_id=job_id,
            status="queued",
            poll_url=f"/idea-jobs/{job_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting idea generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start idea generation"
        )


@app.get("/ideas")
async def get_all_ideas():
    """
    Retrieve all ideas from the database, sorted from newest to oldest.
    Returns:
        List of ideas with details required for displaying on the home page.
    """
    try:
        ideas = db.get_all_ideas()
        return {
            "success": True,
            "data": ideas,
            "count": len(ideas)
        }
    except Exception as e:
        print(f"Error retrieving ideas: {str(e)}")
        return {
            "success": False,
            "error": "Failed to retrieve ideas",
            "data": [],
            "count": 0
        }


@app.get("/ideas/{idea_id}")
async def get_idea_by_id(idea_id: str):
    """
    Retrieve a single idea by its ID with complete details including prompts history.
    Args:
        idea_id: The unique identifier of the idea to retrieve
    Returns:
        Complete idea details including original input, processed analysis,
        ICP data, Reddit analysis, and prompts history.
    """
    try:
        idea = db.get_idea_by_id(idea_id)

        if idea is None:
            raise HTTPException(
                status_code=404,
                detail=f"Idea with ID '{idea_id}' not found"
            )

        try:
            prompts_history = db.get_prompts_metadata_by_idea_id(idea_id)
            idea["prompts_history"] = prompts_history
        except Exception as e:
            print(
                f"Error retrieving prompts history for idea {idea_id}: {str(e)}")
            idea["prompts_history"] = []

        try:
            latest_prompt = db.get_latest_prompt_for_idea_details(
                idea_id, "lovable")
            idea["latest_prompt"] = latest_prompt
        except Exception as e:
            print(
                f"Error retrieving latest prompt for idea {idea_id}: {str(e)}")
            idea["latest_prompt"] = None

        return idea

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving idea {idea_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve idea"
        )


@app.patch("/ideas/{idea_id}")
async def update_idea_field(idea_id: str, update_request: IdeaUpdateRequest):
    """
    Update a specific field of an idea.
    Only one field can be updated per request.
    Args:
        idea_id: The unique identifier of the idea to update
        update_request: Object containing the field to update (only one field should be provided)
    Returns:
        Success status and message
    """
    try:
        update_data = update_request.model_dump(exclude_none=True)

        if len(update_data) != 1:
            raise HTTPException(
                status_code=400,
                detail="Exactly one field must be provided for update"
            )

        field_name, field_value = next(iter(update_data.items()))
        result = db.update_idea_field(idea_id, field_name, field_value)

        if result["success"]:
            return {
                "success": True,
                "message": f"Successfully updated {field_name}"
            }
        else:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            elif "not allowed" in result["error"].lower() or "invalid" in result["error"].lower():
                raise HTTPException(status_code=400, detail=result["error"])
            else:
                raise HTTPException(status_code=500, detail=result["error"])

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error updating idea {idea_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update idea"
        )


@app.patch("/ideas/{idea_id}/lists")
async def update_list(idea_id: str, update_request: UpdateListRequest):
    """
    Update a specific list type of an idea.
    Only one list type can be updated per request.
    Args:
        idea_id: The unique identifier of the idea to update
        update_request: Object containing the list to update (only one list field should be provided)
    Returns:
        Success status and message
    """
    try:
        update_data = update_request.model_dump(exclude_none=True)

        if len(update_data) != 1:
            raise HTTPException(
                status_code=400,
                detail="Exactly one list field must be provided for update"
            )

        list_type, items = next(iter(update_data.items()))

        result = db.update_idea_list(idea_id, list_type, items)

        if result["success"]:
            return {
                "success": True,
                "message": f"Successfully updated {list_type.replace('-', ' ')} ({len(items)} items)"
            }
        else:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            elif any(keyword in result["error"].lower() for keyword in ["invalid", "required", "maximum", "minimum", "at least", "type"]):
                raise HTTPException(status_code=400, detail=result["error"])
            else:
                raise HTTPException(status_code=500, detail=result["error"])

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error updating lists for idea {idea_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to update list")


@app.get("/idea-jobs/{job_id}", response_model=IdeaJobStatusResponse)
async def get_idea_job_status(job_id: str):
    """
    Get status of idea generation job
    """
    try:
        job_data = redis_job_manager.get_job(job_id)

        if not job_data:
            raise HTTPException(
                status_code=410,
                detail="Job has expired or does not exist"
            )

        idea_url = None
        if job_data.get("idea_result_id"):
            idea_url = f"/ideas/{job_data['idea_result_id']}"

        return IdeaJobStatusResponse(
            job_id=job_id,
            status=job_data["status"],
            progress=job_data["progress"],
            error=job_data.get("error"),
            user_id=job_data.get("user_id", "web_user"),
            retry_after=5 if job_data["status"] in [
                "queued", "running"] else None,
            idea_url=idea_url
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting idea job status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get job status"
        )


@app.post("/ideas/{idea_id}/prompts", response_model=PromptGenerateResponse)
async def generate_prompt(
    idea_id: str,
    service_type: str,
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    try:
        valid_services = ["lovable"]
        if service_type not in valid_services:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid service type '{service_type}'. Valid options: {', '.join(valid_services)}"
            )

        idea_data = db.get_idea_by_id(idea_id)
        if not idea_data:
            raise HTTPException(
                status_code=404,
                detail=f"Idea with ID '{idea_id}' not found"
            )

        existing_job_id = redis_job_manager.get_dedupe_job_id(
            idea_id, service_type, idempotency_key)

        if existing_job_id:
            job_data = redis_job_manager.get_job(existing_job_id)
            if job_data:
                by_id_url = None
                if job_data.get("prompt_id"):
                    by_id_url = f"/prompts/{job_data['prompt_id']}"

                return PromptGenerateResponse(
                    job_id=existing_job_id,
                    status=job_data["status"],
                    poll_url=f"/prompt-jobs/{existing_job_id}",
                    result_url=f"/ideas/{idea_id}/prompts/{service_type}",
                    by_id_url=by_id_url
                )

        # Create new job
        job_id = redis_job_manager.create_job(
            idea_id, service_type, idempotency_key)

        # Enqueue Celery task
        generate_prompt_task.delay(job_id)

        return PromptGenerateResponse(
            job_id=job_id,
            status="queued",
            poll_url=f"/prompt-jobs/{job_id}",
            result_url=f"/ideas/{idea_id}/prompts/{service_type}",
            by_id_url=None
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting prompt generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start prompt generation"
        )


@app.get("/prompt-jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    try:
        job_data = redis_job_manager.get_job(job_id)

        if not job_data:
            raise HTTPException(
                status_code=410,
                detail="Job has expired or does not exist"
            )

        by_id_url = None
        if job_data.get("prompt_id"):
            by_id_url = f"/prompts/{job_data['prompt_id']}"

        return JobStatusResponse(
            job_id=job_id,
            status=job_data["status"],
            progress=job_data["progress"],
            error=job_data.get("error"),
            idea_id=job_data["idea_id"],
            service_type=job_data["service_type"],
            result_url=f"/ideas/{job_data['idea_id']}/prompts/{job_data['service_type']}",
            by_id_url=by_id_url,
            retry_after=5 if job_data["status"] in [
                "queued", "running"] else None
        )

    except Exception as e:
        print(f"Error getting job status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get job status"
        )


@app.get("/ideas/{idea_id}/prompts/{service_type}", response_model=PromptResponse)
async def get_latest_prompt(idea_id: str, service_type: str):
    try:
        valid_services = ["lovable"]
        if service_type not in valid_services:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid service type '{service_type}'. Valid options: {', '.join(valid_services)}"
            )

        prompt_data = db.get_latest_prompt(idea_id, service_type)

        if not prompt_data:
            raise HTTPException(
                status_code=404,
                detail=f"No prompt found for idea '{idea_id}' and service '{service_type}'"
            )

        return PromptResponse(
            success=True,
            data=prompt_data,
            message="Prompt retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving latest prompt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve prompt"
        )


@app.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt_by_id(prompt_id: str):
    try:
        prompt_data = db.get_prompt_by_id(prompt_id)

        if not prompt_data:
            raise HTTPException(
                status_code=404,
                detail=f"Prompt with ID '{prompt_id}' not found"
            )

        return PromptResponse(
            success=True,
            data=prompt_data,
            message="Prompt retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving prompt by ID: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve prompt"
        )
