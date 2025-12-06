import streamlit as st
import tempfile
import asyncio
import edge_tts

async def _synthesize(text, voice, file_path):
    tts = edge_tts.Communicate(text, voice=voice, rate="+20%")
    await tts.save(file_path)

def speak(text, voice="id-ID-ArdiNeural"):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    path = temp.name

    asyncio.run(_synthesize(text, voice, path))
    audio = open(path, "rb").read()
    st.audio(audio, format="audio/mp3")
