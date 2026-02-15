import runpod
import base64
import io
import soundfile as sf

# Глобальная переменная для модели
model = None

def get_model():
    global model
    if model is None:
        from qwen_tts import QwenTTS
        model = QwenTTS("Qwen/Qwen3-TTS")
    return model

def handler(job):
    try:
        job_input = job["input"]
        text = job_input.get("text")
        
        if not text:
            return {"error": "Параметр 'text' обязателен"}
        
        language = job_input.get("language", "Russian")
        ref_audio_base64 = job_input.get("ref_audio_base64")
        ref_text = job_input.get("ref_text", "")
        
        if not ref_audio_base64:
            return {"error": "Параметр 'ref_audio_base64' обязателен для клонирования голоса"}
        
        tts = get_model()
        
        # Декодируем аудио
        ref_audio_bytes = base64.b64decode(ref_audio_base64)
        
        with open("/tmp/ref_audio.wav", "wb") as f:
            f.write(ref_audio_bytes)
        
        # Генерируем речь
        audio, sr = tts.synthesize(
            text=text,
            ref_audio="/tmp/ref_audio.wav",
            ref_text=ref_text,
            language=language
        )
        
        # Конвертируем в base64
        buffer = io.BytesIO()
        sf.write(buffer, audio, sr, format='WAV')
        buffer.seek(0)
        audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        return {
            "audio_base64": audio_base64,
            "sample_rate": sr
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

runpod.serverless.start({"handler": handler})
