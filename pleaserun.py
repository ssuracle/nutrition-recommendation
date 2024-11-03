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

# 칼로리 계산 함수
def calculate_bmr(weight, height, age, gender):
    if gender == 'male':
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161

def calculate_daily_calories(bmr, activity_level):
    if activity_level == 'sedentary':
        return bmr * 1.2
    elif activity_level == 'moderate':
        return bmr * 1.55
    elif activity_level == 'active':
        return bmr * 1.725

# Streamlit UI 구성
st.title("개인 맞춤형 식단 및 운동 추천 프로그램")

# 사용자 입력
weight = st.number_input("체중 (kg):", min_value=30, max_value=300, value=70)
height = st.number_input("키 (cm):", min_value=100, max_value=250, value=170)
age = st.number_input("나이:", min_value=1, max_value=120, value=30)
gender = st.selectbox("성별:", ("남성", "여성"))
activity_level = st.selectbox("활동 수준:", ("낮음", "보통", "높음"))
food_list = st.text_area("음식 목록 (쉼표로 구분):", "떡볶이 1인분, 순대 1인분, 라면 1인분")

if st.button("추천 받기"):
    with st.spinner("추천 생성 중..."):
        # BMR 및 일일 칼로리 요구량 계산
        bmr = calculate_bmr(weight, height, age, gender)
        daily_calories = calculate_daily_calories(bmr, activity_level)

        # 음식 목록 번역 및 영양소 정보 가져오기
        translated_food_list = translate_text(food_list)
        foods = [food.strip() for food in translated_food_list.split(',')]
        total_nutrition = {'calories': 0, 'carbs': 0, 'protein': 0, 'fats': 0}

        # 각 음식의 영양 정보 가져오기
        for food in foods:
            nutrition = get_nutrition_from_api(food)
            if nutrition:
                for key in total_nutrition:
                    total_nutrition[key] += nutrition.get(key, 0)

        # OpenAI를 사용하여 맞춤형 피드백 요청
        prompt = (f"사용자가 '{', '.join(foods)}'을(를) 먹고 싶어합니다. "
                  f"총 섭취 칼로리는 {total_nutrition['calories']:.2f}kcal이며, "
                  f"하루 권장 칼로리는 {daily_calories:.2f}kcal입니다. "
                  "이를 기반으로 적절한 운동과 대체 식단 옵션을 포함해 적절한 추천 피드백을 해주세요.")

        feedback = ask_chatgpt(prompt)

        # 사용자 맞춤 피드백 출력
        st.subheader("<사용자 맞춤 피드백>")
        st.markdown(feedback)
