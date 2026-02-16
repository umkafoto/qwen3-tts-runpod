import runpod
import base64
import io
import soundfile as sf
import torch
import numpy as np

# Глобальные переменные
tts_model = None
whisper_model = None

def get_tts_model():
    global tts_model
    if tts_model is None:
        print("Загружаем TTS модель...")
        from qwen_tts import Qwen3TTSModel
        tts_model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
            device_map="cuda:0",
            dtype=torch.bfloat16,
        )
        print("TTS модель загружена!")
    return tts_model

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("Загружаем Whisper модель...")
        import whisper
        whisper_model = whisper.load_model("base", device="cuda")
        print("Whisper модель загружена!")
    return whisper_model

def transcribe_audio(audio_path):
    """Транскрибирует аудио через Whisper"""
    model = get_whisper_model()
    result = model.transcribe(audio_path)
    return result["text"].strip()

def split_text(text, max_chars=1500):
    """Разбивает текст на части по предложениям"""
    import re
    
    # Нормализуем переносы строк
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Разделители предложений
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current = ""
    
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        
        # Если одно предложение длиннее max_chars, разбиваем по запятым
        if len(s) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            
            parts = s.split(',')
            for part in parts:
                part = part.strip()
                if len(current) + len(part) < max_chars:
                    current += part + ", "
                else:
                    if current:
                        chunks.append(current.strip().rstrip(','))
                    current = part + ", "
            continue
        
        if len(current) + len(s) < max_chars:
            current += s + " "
        else:
            if current:
                chunks.append(current.strip())
            current = s + " "
    
    if current:
        chunks.append(current.strip())
    
    return chunks

def handler(job):
    try:
        job_input = job["input"]
        text = job_input.get("text")
        
        if not text:
            return {"error": "Параметр 'text' обязателен"}
        
        language = job_input.get("language", "Russian")
        ref_audio_base64 = job_input.get("ref_audio_base64")
        ref_text = job_input.get("ref_text", "")
        max_chunk_size = job_input.get("max_chunk_size", 1500)
        pause_duration = job_input.get("pause_duration", 0.45)
        
        if not ref_audio_base64:
            return {"error": "Параметр 'ref_audio_base64' обязателен для клонирования голоса"}
        
        # Декодируем аудио
        ref_audio_bytes = base64.b64decode(ref_audio_base64)
        ref_audio_path = "/tmp/ref_audio.mp3"
        
        with open(ref_audio_path, "wb") as f:
            f.write(ref_audio_bytes)
        
        # Если ref_text не передан, транскрибируем через Whisper
        if not ref_text:
            print("Транскрибируем образец голоса...")
            ref_text = transcribe_audio(ref_audio_path)
            print(f"Транскрипция: {ref_text[:100]}...")
        
        tts = get_tts_model()
        
        # Разбиваем текст на части
        chunks = split_text(text, max_chars=max_chunk_size)
        total_chunks = len(chunks)
        print(f"Текст разбит на {total_chunks} частей")
        
        all_audio = []
        sr = None
        
        for i, chunk in enumerate(chunks):
            print(f"Генерируем часть {i+1}/{total_chunks} ({len(chunk)} символов)...")
            
            wavs, sample_rate = tts.generate_voice_clone(
                text=chunk,
                language=language,
                ref_audio=ref_audio_path,
                ref_text=ref_text,
            )
            
            all_audio.append(wavs[0])
            sr = sample_rate
            
            print(f"Часть {i+1}/{total_chunks} готова")
        
        # Склеиваем все части с паузами
        print("Склеиваем аудио...")
        
        pause = np.zeros(int(sr * pause_duration))
        
        audio_with_pauses = []
        for i, audio in enumerate(all_audio):
            audio_with_pauses.append(audio)
            if i < len(all_audio) - 1:
                audio_with_pauses.append(pause)
        
        final_audio = np.concatenate(audio_with_pauses)
        
        # Конвертируем в base64
        buffer = io.BytesIO()
        sf.write(buffer, final_audio, sr, format='WAV')
        buffer.seek(0)
        audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        duration_seconds = len(final_audio) / sr
        
        return {
            "audio_base64": audio_base64,
            "sample_rate": sr,
            "ref_text_used": ref_text,
            "chunks_count": total_chunks,
            "total_chars": len(text),
            "duration_seconds": round(duration_seconds, 2)
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

runpod.serverless.start({"handler": handler})
