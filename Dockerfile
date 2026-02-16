FROM runpod/pytorch:2.2.0-py3.10-cuda12.1.1-devel-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    qwen-tts \
    soundfile \
    runpod \
    torch \
    torchaudio \
    openai-whisper \
    numpy

COPY handler.py /app/handler.py

CMD ["python", "-u", "/app/handler.py"]
