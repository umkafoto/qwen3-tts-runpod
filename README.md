# Qwen3-TTS RunPod Serverless

Serverless endpoint для озвучки текста через Qwen3-TTS на RunPod.

## Быстрый старт

### 1. Форкни этот репозиторий

Нажми "Fork" на GitHub.

### 2. Добавь в RunPod

1. Зайди на [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Нажми **"Add your repo"**
3. Подключи свой GitHub
4. Выбери форкнутый репозиторий
5. Настрой:
   - **GPU**: RTX 4090 или RTX 3090
   - **Min Workers**: 0
   - **Max Workers**: 1-3

### 3. Получи API

После деплоя получишь:
- **Endpoint ID**: `xxxxxxxx`
- **API Key**: в настройках аккаунта

## Использование API

### Python

```python
import runpod
import base64

runpod.api_key = "ваш_api_key"

# Синхронный запрос (ждём результат)
result = runpod.run_sync(
    endpoint_id="ваш_endpoint_id",
    input={
        "text": "Привет! Это тестовая озвучка.",
        "voice": "Vivian",
        "language": "Russian"
    }
)

# Сохраняем аудио
audio_bytes = base64.b64decode(result["audio_base64"])
with open("output.wav", "wb") as f:
    f.write(audio_bytes)
```

### cURL

```bash
curl -X POST "https://api.runpod.ai/v2/ВАШ_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer ВАШ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "Привет мир!",
      "voice": "Vivian",
      "language": "Russian"
    }
  }'
```

### Google Apps Script

```javascript
function generateSpeech(text, voice, language) {
  const ENDPOINT = "https://api.runpod.ai/v2/ВАШ_ENDPOINT_ID/runsync";
  const API_KEY = "ваш_api_key";
  
  const response = UrlFetchApp.fetch(ENDPOINT, {
    method: "POST",
    headers: {
      "Authorization": "Bearer " + API_KEY,
      "Content-Type": "application/json"
    },
    payload: JSON.stringify({
      input: { text, voice, language }
    }),
    muteHttpExceptions: true
  });
  
  const result = JSON.parse(response.getContentText());
  
  if (result.output && result.output.audio_base64) {
    return result.output.audio_base64;
  }
  
  throw new Error(result.error || "Ошибка генерации");
}

// Сохранение в Google Drive
function saveAudioToDrive(base64Audio, filename) {
  const blob = Utilities.newBlob(
    Utilities.base64Decode(base64Audio),
    "audio/wav",
    filename
  );
  return DriveApp.createFile(blob);
}
```

## Параметры запроса

| Параметр | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|--------------|--------------|----------|
| text | string | ✅ | - | Текст для озвучки (до 10000 символов) |
| voice | string | ❌ | "Vivian" | Голос |
| language | string | ❌ | "Russian" | Язык |

## Доступные голоса

- **Vivian** — женский, молодой
- **Ryan** — мужской, молодой  
- **Cherry** — женский, мягкий
- **Ethan** — мужской, зрелый
- **Aria** — женский, нейтральный

## Поддерживаемые языки

Russian, English, Chinese, Japanese, Korean, German, French, Spanish, Portuguese, Italian

## Стоимость

- **Cold start**: ~30-60 сек (первый запрос после простоя)
- **Генерация**: ~$0.0004/сек GPU (RTX 4090)
- **30 мин аудио**: ~$0.15-0.25

## Локальная разработка

```bash
# Клонируй репозиторий
git clone https://github.com/ВАШ_USERNAME/qwen3-tts-runpod.git
cd qwen3-tts-runpod

# Собери образ
docker build -t qwen3-tts .

# Запусти локально
docker run --gpus all -p 8000:8000 qwen3-tts
```

## Лицензия

MIT
