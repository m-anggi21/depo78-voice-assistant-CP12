import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np
import asyncio
import tempfile
import openai
import os
from scipy.io.wavfile import write

openai.api_key = os.getenv("OPENAI_API_KEY")


# =============================
# AUDIO PROCESSOR AUTO STOP
# =============================
class AutoAudioProcessor:
    def __init__(self):
        self.frames = []
        self.silent_counter = 0
        self.max_silence = 15  # 15 frame ≈ 0.7 detik
        self.finished = False
        self.debug_vol = 0

    def recv(self, frame: av.AudioFrame):

        audio = frame.to_ndarray()
        audio_mono = audio.mean(axis=0)

        # Hitung energi suara (lebih akurat daripada abs mean)
        volume = np.sqrt(np.mean(audio_mono**2))
        self.debug_vol = volume  # untuk debugging

        self.frames.append(audio_mono)

        # TUNABLE SILENCE THRESHOLD (lebih baik untuk mic laptop)
        if volume < 30:    # sebelumnya 10 → terlalu rendah
            self.silent_counter += 1
        else:
            self.silent_counter = 0

        if self.silent_counter >= self.max_silence:
            self.finished = True

        return frame


# =============================
# TRANSCRIBE WHISPER
# =============================
def transcribe_audio(frames, sample_rate=48000):

    if not frames:
        return None

    audio_np = np.array(frames).astype(np.float32)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
        write(fp.name, sample_rate, audio_np)
        wav_path = fp.name

    try:
        with open(wav_path, "rb") as f:
            result = openai.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return result.text.strip()
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return None


# =============================
# AUTO VOICE COMPONENT
# =============================
def voice_auto_component(on_text_callback):

    st.markdown("#### 🎙️ Tekan Start, bicara… sistem mendeteksi suara otomatis")

    ctx = webrtc_streamer(
        key="auto-voice",
        mode=WebRtcMode.SENDONLY,
        audio_processor_factory=AutoAudioProcessor,
        media_stream_constraints={"audio": True, "video": False},
    )

    if not ctx.state.playing:
        return

    processor = ctx.audio_processor
    if not processor:
        return

    # Optional debug
    st.caption(f"🎚️ Volume: {processor.debug_vol:.2f}")

    if processor.finished:
        frames = processor.frames
        processor.frames = []
        processor.finished = False
        processor.silent_counter = 0

        text = transcribe_audio(frames)

        if text:
            on_text_callback(text)
        else:
            st.warning("Suara tidak terbaca, silakan ulangi.")
