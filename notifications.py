import requests
import config

def send_telegram_message(message):
    """
    Envía un mensaje a un chat de Telegram.

    Args:
        message (str): El mensaje a enviar.
    """
    if config.TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or config.TELEGRAM_CHAT_ID == "YOUR_TELEGRAM_CHAT_ID":
        print("Advertencia: El token del bot de Telegram o el ID del chat no están configurados. No se enviarán notificaciones.")
        return

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar el mensaje de Telegram: {e}")
