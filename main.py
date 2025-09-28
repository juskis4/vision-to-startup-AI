from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from services.messenger.telegram import TelegramMessenger
from services.llm.openai_llm import OpenAILLM
from services.database.supabase_db import SupabaseDB
from services.agent.agent_service import AgentService
from services.voice.openai_transcriber import OpenAITranscriber

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
