import asyncio
import websockets
import json
import math
import struct

async def main():
    uri = "ws://127.0.0.1:8000/api/interview/stream?session_id=sess_c3fa40d7"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket.")
            
            print("Skipping wait for initial audio, sending sine wave immediately...")
                
            # 2. Generate a 16kHz PCM sine wave (beep) for 2 seconds
            print("Sending 2 seconds of loud audio (sine wave) to trigger VAD...")
            sample_rate = 16000
            duration = 2.0
            t = [i / sample_rate for i in range(int(sample_rate * duration))]
            # 440 Hz sine wave, loud volume
            audio_samples = [int(30000 * math.sin(2 * math.pi * 440 * x)) for x in t]
            audio_bytes = struct.pack(f"<{len(audio_samples)}h", *audio_samples)
            
            # Send in chunks of 4096 frames (like frontend)
            chunk_size = 4096 * 2 # 2 bytes per frame
            for i in range(0, len(audio_bytes), chunk_size):
                await websocket.send(audio_bytes[i:i+chunk_size])
                await asyncio.sleep(0.2) # simulate real-time
                
            # 3. Send 3 seconds of silence to trigger processing
            print("Sending 3 seconds of silence to trigger end-of-speech...")
            silence_samples = [0 for _ in range(int(sample_rate * 3.0))]
            silence_bytes = struct.pack(f"<{len(silence_samples)}h", *silence_samples)
            for i in range(0, len(silence_bytes), chunk_size):
                await websocket.send(silence_bytes[i:i+chunk_size])
                await asyncio.sleep(0.2)
                
            # 4. Wait for response
            print("Waiting for server response after processing...")
            msg = await asyncio.wait_for(websocket.recv(), timeout=20.0)
            resp = json.loads(msg)
            if "serverContent" in resp:
                print("Success! Received response audio back!")
            else:
                print("Received something else:", resp)
                
    except Exception as e:
        print("Test failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
