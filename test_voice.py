import asyncio
import websockets
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No API Key")
        return

    uri = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={api_key}"
    try:
        print("Connecting to Gemini...")
        async with websockets.connect(uri) as ws:
            setup_msg = {
                "setup": {
                    "model": "models/gemini-omni-flash-preview",
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Puck"}}}
                    }
                }
            }
            await ws.send(json.dumps(setup_msg))
            response = await ws.recv()
            print("Setup response:", response)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gemini())
