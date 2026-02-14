"""
RunPod Serverless Handler для Qwen3-TTS Voice Cloning
"""

import runpod
import torch
import soundfile as sf
import base64
import io
import os
import tempfile

model = None

def load_model():
    global model
    if model is None:
        from qwen_tts import Qwen3TTSModel
        
        print("Загружаем модель для клонирования голоса...")
        model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base",  # Base модель для клонирования!
            device="cuda",
            torch_dtype=torch.bfloat16
        )
        print("Модель загружена!")
    
    return model


def handler(job):
    job_input = job.get("input", {})
    
    text = job_input.get("text", "")
    ref_audio_base64 = job_input.get("ref_audio_base64", "")
    ref_text = job_input.get("ref_text", "")
    language = job_input.get("language", "Russian")
    
    if not text:
        return {"error": "Параметр 'text' обязателен"}
    
    if not ref_audio_base64:
        return {"error": "Параметр 'ref_audio_base64' обязателен для клонирования голоса"}
    
    try:
        model = load_model()
        
        # Декодируем reference audio
        ref_audio_bytes = base64.b64decode(ref_audio_base64)
        
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(ref_audio_bytes)
            ref_audio_path = f.name
        
        # Генерация с клонированием голоса
        audio = model.generate(
            text=text,
            ref_audio=ref_audio_path,
            ref_text=ref_text if ref_text else None,
            language=language
        )
        
        # Удаляем временный файл
        os.unlink(ref_audio_path)
        
        # Конвертируем в base64
        buffer = io.BytesIO()
        sf.write(buffer, audio, 24000, format="WAV")
        buffer.seek(0)
        audio_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        return {
            "audio_base64": audio_base64,
            "sample_rate": 24000,
            "format": "wav",
            "text_length": len(text)
        }
        
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
