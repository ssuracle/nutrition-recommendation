import os
import streamlit as st
from google.cloud import translate_v2 as translate
import requests
import json

# Load secrets from Streamlit secrets management
openai_api_key = st.secrets["general"]["OPENAI_API_KEY"]
google_api_credentials = st.secrets["google"]["GOOGLE_APPLICATION_CREDENTIALS"]

# Set Google API credentials
with open("google_credentials.json", "w") as f:
    f.write(google_api_credentials)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_credentials.json"

# Initialize Google Translate Client
translate_client = translate.Client()

# 번역 함수 정의
def translate_text(text, target_language='en'):
    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']

# 예시 번역 출력
paragraph_french = "떡볶이 1인분, 오뎅 3개"
translated_text = translate_text(paragraph_french)
st.write(translated_text)

# OpenAI API 관련 설정
def ask_chatgpt(prompt):
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    content = response.json()
    return content['choices'][0]['message']['content'].strip()

# 사용자 정보 및 음식 목록 설정
user_info = {
    'weight': 100,  # 체중 kg
    'height': 170,  # 키 cm
    'age': 54,      # 나이
    'gender': 'male',  # 성별
    'activity_level': 'active'  # 활동 수준
}

food_list = ["떡볶이 1인분", "순대 1인분", "라면 1인분"]

# GPT에 질문할 프롬프트 생성
prompt = f"사용자가 '{', '.join(food_list)}'을(를) 먹고 싶어합니다. "
response = ask_chatgpt(prompt)

# 결과 표시
st.write("사용자 맞춤 피드백")
st.write(response)
