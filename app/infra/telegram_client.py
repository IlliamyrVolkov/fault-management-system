import requests
from app.core.config import settings
from app.core.logger import logger


def send_telegram_alert(device_name: str, ip_address: str, severity: str, message: str):
    token = settings.telegram.bot_token
    chat_id = settings.telegram.chat_id

    if not token or not chat_id:
        logger.error("Не налаштовано токени Telegram у файлі .env")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    icon = "🔴" if severity.upper() == "CRITICAL" else "⚠️"

    text = (
        f"{icon} <b>FAULT ALERT: {severity.upper()}</b>\n"
        f"<b>Пристрій:</b> {device_name}\n"
        f"<b>IP Адреса:</b> {ip_address}\n"
        f"<b>Деталі:</b> {message}"
    )

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        logger.success(f"Сповіщення успішно надіслано в Telegram для {device_name}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка відправки Telegram сповіщення: {e}")
        return False


if __name__ == "__main__":
    logger.info("Тестування відправки Telegram повідомлення...")
    send_telegram_alert(
        device_name="Border_Router",
        ip_address="192.168.1.1",
        severity="CRITICAL",
        message="Втрачено 3 ICMP пакети підряд. Вузол недоступний."
    )