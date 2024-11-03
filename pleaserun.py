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
        "model": "gpt-4o-mini-2024-07-18",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    content = response.json()
    return content['choices'][0]['message']['content'].strip()

# BMR 계산 함수 정의
def calculate_bmr(weight, height, age, gender):
    if gender == '남성':
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161

# 일일 칼로리 요구량 계산 함수 정의
def calculate_daily_calories(bmr, activity_level):
    if activity_level == '낮음':
        return bmr * 1.2
    elif activity_level == '보통':
        return bmr * 1.55
    elif activity_level == '높음':
        return bmr * 1.725

# 음식 영양 정보 가져오기 함수 정의
def get_nutrition_from_api(food):
    nutritionix_app_id = st.secrets["nutritionix"]["APP_ID"]
    nutritionix_api_key = st.secrets["nutritionix"]["API_KEY"]
    
    api_url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": nutritionix_app_id,
        "x-app-key": nutritionix_api_key,
        "Content-Type": "application/json"
    }
    data = {"query": food}

    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        nutrients = response.json()['foods'][0]
        return {
            'calories': nutrients['nf_calories'],
            'carbs': nutrients['nf_total_carbohydrate'],
            'protein': nutrients['nf_protein'],
            'fats': nutrients['nf_total_fat']
        }
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
        return None
    except Exception as err:
        st.error(f"An error occurred: {err}")
        return None

# Streamlit UI 설정
st.title("개인 맞춤형 식단 및 운동 추천 프로그램")

# 사용자 정보 입력
weight = st.number_input("체중 (kg):", min_value=0.0, step=0.1, value=0.0)
height = st.number_input("키 (cm):", min_value=0.0, step=0.1, value=0.0)
age = st.number_input("나이:", min_value=0, step=1, value=0)
gender = st.selectbox("성별:", options=["선택하세요", "남성", "여성"])
activity_level = st.selectbox("활동 수준:", options=["선택하세요", "낮음", "보통", "높음"])

# 음식 목록 입력
food_list = st.text_area("음식 목록 (쉼표로 구분):", "")

if st.button("추천 받기"):
    if gender == "선택하세요" or activity_level == "선택하세요" or not food_list:
        st.warning("모든 정보를 올바르게 입력해 주세요.")
    else:
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



            # Streamlit UI에서 버튼 추가
            if st.button("맞춤 피드백 음성으로 듣기"):
                if feedback:
                    tts(feedback)
                    st.success("맞춤 피드백이 음성으로 변환되었습니다.")
                else:
                    st.warning("맞춤 피드백이 없습니다.")


