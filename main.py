from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import os
import requests

load_dotenv()
app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# -------------------------
# WhatsApp Send Text Message
# -------------------------
def send_whatsapp_text(to_number, message_text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Text Response:", response.status_code, response.text)

# -------------------------
# WhatsApp Send Buttons (Max 3)
# -------------------------
def send_whatsapp_buttons(to_number):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "📋 Please choose an option:"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "portfolio_btn",
                            "title": "📊 Portfolio"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "fund_btn",
                            "title": "📈 Fund Updates"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "sip_btn",
                            "title": "💰 SIP Updates"
                        }
                    }
                ]
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Button Response:", response.status_code, response.text)

# -------------------------
# Intent Mapping
# -------------------------
def interpret_message(text: str) -> str:
    text = text.lower()
    if "portfolio" in text:
        return "get_portfolio"
    elif "sip" in text:
        return "get_sip_updates"
    elif "transaction" in text:
        return "get_transaction_history"
    elif "nav" in text or "fund" in text:
        return "get_fund_nav"
    elif "exit" in text:
        return "get_exit_help"
    elif "help" in text or "menu" in text:
        return "show_help"
    else:
        return "unknown"

# -------------------------
# Webhook Verification (GET)
# -------------------------
@app.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    challenge: str = Query(None, alias="hub.challenge"),
    verify_token: str = Query(None, alias="hub.verify_token")
):
    if mode == "subscribe" and verify_token == VERIFY_TOKEN:
        return challenge
    return PlainTextResponse("unauthorized", status_code=403)

# -------------------------
# Webhook Receiver (POST)
# -------------------------
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()

    # Log payload safely with UTF-8 encoding
    with open("webhook_logs.txt", "a", encoding="utf-8") as f:
        f.write(str(data) + "\n\n")

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]["value"]

        if "messages" in changes:
            message = changes["messages"][0]
            phone_number = message["from"]

            if message["type"] == "text":
                message_text = message["text"]["body"]
                intent = interpret_message(message_text)

                # Respond based on text intent
                if intent == "get_portfolio":
                    send_whatsapp_text(phone_number, "📊 Your portfolio is 50% Equity, 30% Debt, 20% Gold.")
                elif intent == "get_sip_updates":
                    send_whatsapp_text(phone_number, "💰 Your SIP of ₹5,000 runs on 5th of every month.")
                elif intent == "get_transaction_history":
                    send_whatsapp_text(phone_number, "🧾 Last 3 transactions:\n- ₹5,000 SIP\n- ₹1,000 Redemption\n- ₹15,000 Purchase")
                elif intent == "get_fund_nav":
                    send_whatsapp_text(phone_number, "📈 NAV for Axis Bluechip Fund: ₹102.45 (today)")
                elif intent == "get_exit_help":
                    send_whatsapp_text(phone_number, "❌ Exit your funds via the InvestWell dashboard. Need a link?")
                elif intent == "show_help":
                    send_whatsapp_buttons(phone_number)
                else:
                    send_whatsapp_text(phone_number, "🤖 I didn’t understand that. Tap *Help* or *Menu* for options.")
                    send_whatsapp_buttons(phone_number)

            elif message["type"] == "interactive":
                button_id = message["interactive"]["button_reply"]["id"]

                if button_id == "portfolio_btn":
                    send_whatsapp_text(phone_number, "📊 Your portfolio is 50% Equity, 30% Debt, 20% Gold.")
                elif button_id == "fund_btn":
                    send_whatsapp_text(phone_number, "📈 NAV for Axis Bluechip Fund: ₹102.45 (today)")
                elif button_id == "sip_btn":
                    send_whatsapp_text(phone_number, "💰 Your SIP of ₹5,000 runs on 5th of every month.")
                else:
                    send_whatsapp_text(phone_number, "🤔 Unknown button selected.")
        else:
            print("⚠️ No new messages. This is likely a status update.")

    except Exception as e:
        print("❗ Error handling message:", e)

    return {"status": "received"}
