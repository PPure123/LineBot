from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import joblib
import pandas as pd
import numpy as np

app = Flask(__name__)

# ตั้งค่า LINE Bot
line_bot_api = LineBotApi('LpmHQuG1ysrCROY7VBm0P3xJx4kX1Tj/9Al3VrWWQpgos65TINW8mB6HjQISBIXs0XJPw3jZ5Ei/YsvS7mDcRD5SrkUiRvVmPRaLQ9qG0g7Z+TjNV2pBlO3qbifNPmGpfD0nMxIHjnKSV/yuWhcOzgdB04t89/1O/w1cDnyilFU=')  # ใส่ Channel Access Token ให้ถูก
handler = WebhookHandler('71f2e917d53cc1b25404b8de59fd6cb9')         # ใส่ Channel Secret ให้ถูก

# โหลดโมเดลและ scaler
model = joblib.load("D:\LineBot\gradient_boosting_model.pkl")
scaler = joblib.load("D:\LineBot\scaler.pkl")

# เก็บข้อมูลผู้ใช้
user_data = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    print("Received body:", body)  # ดีบั๊กดูข้อมูลที่ LINE ส่งมา
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature - Check Channel Secret")
        return 'OK', 200  # คืน 200 แม้ signature ผิด
    except Exception as e:
        print(f"Error: {str(e)}")
        return 'OK', 200  # คืน 200 ถ้ามี error อื่น
    return 'OK', 200  # คืน 200 เสมอ

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    if user_id not in user_data:
        user_data[user_id] = {'step': 0}

    step = user_data[user_id]['step']
    reply_text = ""

    try:
        if step == 0:
            reply_text = "สวัสดี! กรุณาเลือกเพศ (0=หญิง, 1=ชาย)"
            user_data[user_id]['step'] = 1
        elif step == 1:
            user_data[user_id]['gender'] = int(text)
            reply_text = "กรุณาบอกอายุ (เช่น 45.5)"
            user_data[user_id]['step'] = 2
        elif step == 2:
            user_data[user_id]['age'] = float(text)
            reply_text = "คุณมีภาวะความดันโลหิตสูงหรือไม่? (0=ไม่มี, 1=มี)"
            user_data[user_id]['step'] = 3
        elif step == 3:
            user_data[user_id]['hypertension'] = int(text)
            reply_text = "คุณเป็นโรคหัวใจหรือไม่? (0=ไม่มี, 1=มี)"
            user_data[user_id]['step'] = 4
        elif step == 4:
            user_data[user_id]['heart_disease'] = int(text)
            reply_text = "คุณเคยแต่งงานหรือไม่? (0=ไม่เคย, 1=เคย)"
            user_data[user_id]['step'] = 5
        elif step == 5:
            user_data[user_id]['ever_married'] = int(text)
            reply_text = "กรุณาระบุระดับกลูโคสเฉลี่ย (เช่น 120.5)"
            user_data[user_id]['step'] = 6
        elif step == 6:
            user_data[user_id]['avg_glucose_level'] = float(text)
            reply_text = "กรุณาระบุค่า BMI (เช่น 25.0)"
            user_data[user_id]['step'] = 7
        elif step == 7:
            user_data[user_id]['bmi'] = float(text)

            input_dict = {
                'gender': user_data[user_id]['gender'],
                'age': user_data[user_id]['age'],
                'hypertension': user_data[user_id]['hypertension'],
                'heart_disease': user_data[user_id]['heart_disease'],
                'ever_married': user_data[user_id]['ever_married'],
                'avg_glucose_level': user_data[user_id]['avg_glucose_level'],
                'bmi': user_data[user_id]['bmi']
            }
            input_df = pd.DataFrame([input_dict])
            input_scaled = scaler.transform(input_df)
            prediction = model.predict(input_scaled)[0]

            reply_text = "มีความเสี่ยงเป็นโรคหลอดเลือดสมอง" if prediction == 1 else "ไม่มีความเสี่ยงเป็นโรคหลอดเลือดสมอง"
            del user_data[user_id]

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

    except ValueError:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="กรุณาใส่ข้อมูลให้ถูกต้อง (ตัวเลขเท่านั้น)"))
    except Exception as e:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"เกิดข้อผิดพลาด: {str(e)}"))

# Vercel handler
def handler(request):
    return app(request.environ, request.start_response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    
model = joblib.load("gradient_boosting_model.pkl")
scaler = joblib.load("scaler.pkl")