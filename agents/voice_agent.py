from config.settings import settings
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
from openai import AsyncOpenAI
import tempfile
import os
from pathlib import Path
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceRequest(BaseModel):
    text: str
    voice: str = "alloy"
    speed: float = 1.0

class TranscriptionResponse(BaseModel):
    text: str
    confidence: float
    language: str
    duration: float

app = FastAPI(title="Voice Agent", description="Advanced speech processing service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VoiceService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self._validate_openai_setup()

    def _validate_openai_setup(self):
        if not self.openai_client:
            logger.warning("⚠️ OpenAI API key not configured - voice services will be limited")
        else:
            logger.info("✅ OpenAI client initialized successfully")

    async def transcribe_audio_openai(self, file_path: str, original_filename: str) -> TranscriptionResponse:
        if not self.openai_client:
            raise HTTPException(status_code=500, detail="OpenAI API not configured")

        try:
            if not os.path.exists(file_path):
                raise HTTPException(status_code=500, detail="Audio file not found")
            
            file_size = os.path.getsize(file_path)
            logger.info(f"Processing audio file: {original_filename}, size: {file_size} bytes")
            
            if file_size > 25 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File too large (max 25MB)")

            with open(file_path, 'rb') as audio_file:
                # Add retry logic for OpenAI API calls
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        transcript = await self.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=(original_filename, audio_file, "audio/mpeg"),
                            response_format="verbose_json"
                        )
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise e
                        logger.warning(f"Transcription attempt {attempt + 1} failed: {e}")
                        await asyncio.sleep(1)
            
            result = TranscriptionResponse(
                text=transcript.text.strip(),
                confidence=0.95,  # Whisper doesn't provide confidence scores
                language=transcript.language or "unknown",
                duration=transcript.duration or 0.0
            )
            
            logger.info(f"Transcription successful: '{result.text[:50]}...'")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    async def synthesize_speech(self, request: VoiceRequest) -> str:
        if not self.openai_client:
            raise HTTPException(status_code=500, detail="OpenAI API not configured")

        try:
            logger.info(f"Synthesizing speech: '{request.text[:50]}...' with voice '{request.voice}'")
            
            # Add retry logic for OpenAI API calls
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = await self.openai_client.audio.speech.create(
                        model="tts-1",
                        voice=request.voice,
                        input=request.text,
                        speed=request.speed
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"TTS attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(1)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_file.write(response.content)
            temp_file.close()

            logger.info(f"Speech synthesis successful, file: {temp_file.name}")
            return temp_file.name

        except Exception as e:
            logger.error(f"Speech synthesis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")

voice_service = VoiceService()

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    temp_file_path = None
    try:
        logger.info(f"Received transcription request: {file.filename}, content-type: {file.content_type}")
        
        allowed_extensions = ['.wav', '.mp3', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm']
        file_ext = os.path.splitext(file.filename.lower())[1] if file.filename else ''
        
        if not file.content_type or not file.content_type.startswith('audio/'):
            if file_ext not in allowed_extensions:
                raise HTTPException(status_code=400, detail=f"Unsupported file format. Allowed: {allowed_extensions}")

        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 25MB)")

        file_extension = file_ext or '.wav'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        temp_file_path = temp_file.name
        temp_file.write(content)
        temp_file.close()
        
        result = await voice_service.transcribe_audio_openai(temp_file_path, file.filename)
        return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal server error in transcribe_audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file_path}: {e}")

@app.post("/synthesize")
async def synthesize_speech(request: VoiceRequest):
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        # Limit text length to prevent extremely long TTS requests
        if len(request.text) > 4000:
            request.text = request.text[:4000] + "..."
            logger.warning("Text truncated to 4000 characters for TTS")

        audio_file_path = await voice_service.synthesize_speech(request)

        return FileResponse(
            audio_file_path,
            media_type="audio/mpeg",
            filename="response.mp3",
            background=lambda: os.unlink(audio_file_path) if os.path.exists(audio_file_path) else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal server error in synthesize_speech: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voices")
async def get_available_voices():
    return {
        "voices": [
            {"id": "alloy", "name": "Alloy", "gender": "neutral", "description": "Balanced, versatile voice"},
            {"id": "echo", "name": "Echo", "gender": "male", "description": "Clear, professional male voice"},
            {"id": "fable", "name": "Fable", "gender": "female", "description": "Warm, storytelling female voice"},
            {"id": "onyx", "name": "Onyx", "gender": "male", "description": "Deep, authoritative male voice"},
            {"id": "nova", "name": "Nova", "gender": "female", "description": "Bright, energetic female voice"},
            {"id": "shimmer", "name": "Shimmer", "gender": "female", "description": "Gentle, soothing female voice"}
        ],
        "default": "alloy"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "openai_available": voice_service.openai_client is not None,
        "services": {
            "transcription": "available" if voice_service.openai_client else "unavailable",
            "speech_synthesis": "available" if voice_service.openai_client else "unavailable"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)