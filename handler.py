"""
RunPod Serverless Handler для Qwen3-TTS
Озвучка текста через API
"""

import runpod
import torch
import soundfile as sf
import base64
import io
import os

# Глобальная переменная для модели
model = None

def load_model():
    """Загрузка модели при первом запросе"""
    global model
    if model is None:
        from qwen_tts import Qwen3TTSModel
        
        model_name = os.environ.get(
            "MODEL_NAME", 
            "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
        )
        
        print(f"Загружаем модель: {model_name}")
        model = Qwen3TTSModel.from_pretrained(
            model_name,
            device="cuda",
            torch_dtype=torch.bfloat16
        )
        print("Модель загружена!")
    
    return model


def generate_speech(text, voice="Vivian", language="Russian", speed=1.0):
    """Генерация аудио из текста"""
    model = load_model()
    
    # Генерация
    audio = model.generate(
        text=text,
        speaker=voice,
        language=language
    )
    
    # Конвертируем в WAV base64
    buffer = io.BytesIO()
    sf.write(buffer, audio, 24000, format="WAV")
    buffer.seek(0)
    audio_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    return audio_base64


def handler(job):
    """
    Основной обработчик запросов RunPod
    
    Input:
        text: str - текст для озвучки
        voice: str - голос (Vivian, Ryan, Cherry, Ethan, Aria и др.)
        language: str - язык (Russian, English, Chinese, Japanese и др.)
        
    Output:
        audio_base64: str - аудио в формате base64 WAV
        sample_rate: int - частота дискретизации (24000)
    """
    job_input = job.get("input", {})
    
    # Получаем параметры
    text = job_input.get("text", "")
    voice = job_input.get("voice", "Vivian")
    language = job_input.get("language", "Russian")
    
    # Валидация
    if not text:
        return {"error": "Параметр 'text' обязателен"}
    
    if len(text) > 10000:
        return {"error": "Текст слишком длинный (максимум 10000 символов)"}
    
    try:
        # Генерируем аудио
        audio_base64 = generate_speech(
            text=text,
            voice=voice,
            language=language
        )
        
        return {
            "audio_base64": audio_base64,
            "sample_rate": 24000,
            "format": "wav",
            "text_length": len(text),
            "voice": voice,
            "language": language
        }
        
    except Exception as e:
        return {"error": str(e)}


# Запуск serverless worker
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
