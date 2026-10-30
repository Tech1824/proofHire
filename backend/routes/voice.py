from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
import os
import asyncio
import base64
import struct
import math
import google.generativeai as genai

try:
    from db import crud
    from ai.api import submit_answer
except ImportError:
    pass # For testing without db

router = APIRouter(prefix="/api/interview", tags=["voice"])

def calculate_rms(audio_bytes):
    count = len(audio_bytes) // 2
    if count == 0: return 0
    shorts = struct.unpack(f"<{count}h", audio_bytes)
    sum_squares = sum(s * s for s in shorts)
    return math.sqrt(sum_squares / count)

def pcm_to_wav(pcm_data, sample_rate=16000, num_channels=1, sampwidth=2):
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + len(pcm_data),
        b'WAVE',
        b'fmt ',
        16,
        1,
        num_channels,
        sample_rate,
        sample_rate * num_channels * sampwidth,
        num_channels * sampwidth,
        sampwidth * 8,
        b'data',
        len(pcm_data)
    )
    return header + pcm_data

async def generate_tts_base64(text: str) -> str:
    import edge_tts
    communicate = edge_tts.Communicate(text, 'en-US-AriaNeural')
    audio_data = b''
    async for chunk in communicate.stream():
        if chunk['type'] == 'audio':
            audio_data += chunk['data']
    return base64.b64encode(audio_data).decode("utf-8")

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket, session_id: str = Query(None)):
    await websocket.accept()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found.", flush=True)
        await websocket.close()
        return
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    print(f"Pipeline Voice WebSocket connected. Session: {session_id}", flush=True)
    
    # Read the latest question and speak it immediately
    if session_id:
        session = crud.get_session(session_id)
        if session:
            turns = session.get("turns", [])
            if turns:
                latest = turns[-1]
                question_text = latest.get("question_text", "")
                if question_text:
                    try:
                        b64 = await generate_tts_base64(question_text)
                        await websocket.send_json({
                            "serverContent": {
                                "modelTurn": {
                                    "parts": [{"inlineData": {"data": b64}}]
                                }
                            }
                        })
                    except Exception as e:
                        print(f"Initial TTS error: {e}", flush=True)

    audio_buffer = bytearray()
    silence_frames = 0
    speaking = False
    THRESHOLD = 500  # Adjust as needed based on mic volume

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message:
                chunk = message["bytes"]
                rms = calculate_rms(chunk)
                
                if rms > THRESHOLD:
                    speaking = True
                    silence_frames = 0
                    audio_buffer.extend(chunk)
                elif speaking:
                    silence_frames += 1
                    audio_buffer.extend(chunk)
                    
                    if silence_frames > 8: # roughly 2 seconds of silence
                        print(f"Processing {len(audio_buffer, flush=True)} bytes of audio...")
                        
                        # Process audio
                        wav_data = pcm_to_wav(audio_buffer)
                        
                        # Use Gemini to transcribe
                        try:
                            response = model.generate_content([
                                "Transcribe the following audio accurately. Just output the candidate's words, nothing else.",
                                {"mime_type": "audio/wav", "data": wav_data}
                            ])
                            transcript = response.text.strip()
                            print(f"Transcript: {transcript}", flush=True)
                            
                            if transcript and session_id:
                                # Submit answer to pipeline
                                res = submit_answer(session_id, transcript, None)
                                
                                next_text = ""
                                if res.get("status") == "done":
                                    next_text = "Interview complete. Thank you."
                                else:
                                    next_text = res.get("next", {}).get("text", "")
                                    
                                if next_text:
                                    b64 = await generate_tts_base64(next_text)
                                    await websocket.send_json({
                                        "serverContent": {
                                            "modelTurn": {
                                                "parts": [{"inlineData": {"data": b64}}]
                                            }
                                        }
                                    })
                                    
                        except Exception as e:
                            print(f"Processing Error: {e}", flush=True)
                            
                        # Reset
                        audio_buffer = bytearray()
                        speaking = False

    except WebSocketDisconnect:
        print("Client disconnected.", flush=True)
    except Exception as e:
        import traceback
        print(f"Connection error: {e}", flush=True)
        traceback.print_exc()
