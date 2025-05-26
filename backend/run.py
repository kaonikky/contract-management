import uvicorn
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем порт из переменных окружения или используем порт 8000 по умолчанию
PORT = int(os.getenv("PORT", 8000))

if __name__ == "__main__":
    # Запускаем сервер
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,  # Автоматическая перезагрузка при изменении кода
        workers=1     # Количество рабочих процессов
    )