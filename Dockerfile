FROM runpod/pytorch:2.2.0-py3.10-cuda12.1.1-devel-ubuntu22.04

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir \
    qwen-tts \
    soundfile \
    runpod \
    torch \
    torchaudio

# Опционально: предзагрузка модели (ускоряет холодный старт, но увеличивает размер образа)
# Раскомментируй если хочешь включить модель в образ:
# RUN python -c "from qwen_tts import Qwen3TTSModel; Qwen3TTSModel.from_pretrained('Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice')"

# Копируем handler
COPY src/handler.py /app/handler.py

# Переменные окружения
ENV MODEL_NAME="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
ENV PYTHONUNBUFFERED=1

# Запуск
CMD ["python", "-u", "/app/handler.py"]
