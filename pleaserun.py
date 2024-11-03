import os
import streamlit as st
from google.cloud import translate_v2 as translate
import requests
import json

# Streamlit 비밀 관리에서 API 키 로드
openai_api_key = st.secrets["general"]["OPENAI_API_KEY"]
google_api_credentials = st.secrets["google"]["GOOGLE_APPLICATION_CREDENTIALS"]

# Google API 자격증명 설정
with open("google_credentials.json", "w") as f:
    f.write(google_api_credentials)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_credentials.json"

# Google Translate 클라이언트 초기화
translate_client = translate.Client()

# 번역 함수 정의
def translate_text(text, target_language='en'):
    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']

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

# Streamlit UI 설정
st.title("개인 맞춤형 식단 및 운동 추천 프로그램")

# 사용자 정보 입력
weight = st.number_input("체중 (kg):", min_value=0.0)
height = st.number_input("키 (cm):", min_value=0.0)
age = st.number_input("나이:", min_value=0)
gender = st.selectbox("성별:", options=["남성", "여성"])
activity_level = st.selectbox("활동 수준:", options=["낮음", "보통", "높음"])

# 음식 목록 입력
food_list_input = st.text_area("음식 목록 (예: 떡볶이 1인분, 순대 1인분):")
food_list = food_list_input.split(",") if food_list_input else []

# 버튼 클릭 시 피드백 요청
if st.button("추천 받기"):
    # 사용자 정보 사전 생성
    user_info = {
        'weight': weight,
        'height': height,
        'age': age,
        'gender': gender,
        'activity_level': activity_level.lower()  # 소문자로 변환하여 일관성 유지
    }

    # GPT에 질문할 프롬프트 생성
    prompt = f"사용자가 '{', '.join(food_list)}'을(를) 먹고 싶어합니다."
    response = ask_chatgpt(prompt)

    # 결과 표시
    st.write("사용자 맞춤 피드백")
    st.write(response)
