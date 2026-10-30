# ProofHire V3: Voice-to-Voice (V2V) Implementation Plan

## Architectural Overview
The goal of V3 is to upgrade the ProofHire interview experience from a text-based, turn-based UI to a **real-time, fully duplex Voice-to-Voice** interface. 

To ensure maximum resilience and zero cost for the prototype, we will implement a dual-engine strategy:
1. **Primary Engine:** Native Multimodal Audio (Google Gemini Multimodal Live API via WebSockets).
2. **Fallback Engine:** Pipelined Architecture (Local Whisper STT + Text LLM + Free TTS).

---

## 🛠️ Phase I: The Transport Layer & Fallback Setup
*Before connecting the complex Gemini Live socket, we must establish a reliable audio pipeline.*

### Backend Tasks:
- [ ] Add `websockets` and `pyaudio` dependencies to `requirements.txt`.
- [ ] Create `backend/routes/voice.py` containing a new `WebSocket` endpoint `/api/interview/stream`.
- [ ] Implement audio chunk re-assembly: Receive chunks of `int16` PCM audio from the frontend.
- [ ] **Build Fallback Pipeline:** Integrate a free, local STT model (e.g., `faster-whisper`) to convert received audio into text. Pass the text to our existing `ai_api.py` graph logic, then pipe the string to a lightweight TTS library (e.g., `edge-tts` or `gTTS`) and stream the resulting audio bytes back to the client.

### Frontend Tasks:
- [ ] Update `app.js` to prompt for microphone permissions (`navigator.mediaDevices.getUserMedia`).
- [ ] Implement a `MediaRecorder` or `AudioWorkletProcessor` to slice raw mic input into chunks and emit them over a native `WebSocket` connection.
- [ ] Implement an audio queue to playback the incoming `ArrayBuffer` audio chunks seamlessly.
- [ ] **UI Refresh:** Convert the `renderDepth()` text view into a "Call" interface. Add mute/unmute buttons, an animated audio visualizer (using `AnalyserNode`), and a prominent "End Interview" button.

---

## 🚀 Phase J: Gemini Multimodal Live API Integration
*With the WebSocket plumbing verified, we swap the Pipelined Fallback for the lightning-fast Gemini Native engine.*

### Backend Tasks:
- [ ] Install the `google-genai` SDK for WebRTC/WebSocket support.
- [ ] In `/api/interview/stream`, intercept the connection and proxy it directly to `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent`.
- [ ] **Session Initialization:** Send the candidate's Knowledge Graph (`graph_json`) as the initial `system_instruction` in the `setup` message to Gemini, anchoring the AI to the codebase just like we do in text.
- [ ] Stream incoming client PCM chunks wrapped in `RealtimeInput` messages to Gemini.
- [ ] Receive `serverContent` messages containing model audio output and proxy them back to the frontend to play.

### Frontend Tasks:
- [ ] Add "Turn Detection": Since Gemini Live is fully duplex, handle server interruption messages gracefully if the candidate speaks over the AI.
- [ ] Fine-tune the audio visualizer to respond cleanly to Gemini's specific frequency bands.

---

## Technical Constraints & Edge Cases
- **Audio Formats:** Gemini Live strictly expects `pcm_16bit` at `16000Hz` or `24000Hz`. The frontend `AudioContext` must explicitly resample microphone input to match this before sending over the wire.
- **State Management:** Unlike text where state is explicitly tracked per turn in the DB, Gemini Live manages its own conversational history during the active socket. At the end of the session, we must instruct Gemini to output a final JSON summary of the interview to save as evidence in SQLite.
