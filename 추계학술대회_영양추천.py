import os
import streamlit as st
import requests
from google.cloud import translate_v2 as translate


# Streamlit Secrets에서 API 키 가져오기
openai_api_key = st.secrets["OPENAI_API_KEY"]
google_api_credentials = st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]

# Google Cloud 인증 설정
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_api_credentials

# Google Cloud Translate 클라이언트 생성
translate_client = translate.Client()

# Streamlit 앱 설정
st.title("맞춤형 식단 추천 앱")
st.write("식단 추천을 위해 원하는 음식을 입력하세요:")

# 음식 목록 입력 받기
food_input = st.text_area("음식 목록 (예: 떡볶이, 순대, 라면 등)", "떡볶이, 순대, 라면")
submit_button = st.button("추천 받기")

# 추천 버튼 클릭 시 실행
if submit_button:
    food_list = [food.strip() for food in food_input.split(",")]
    
    # 총 섭취 영양소 계산
    total_intake = calculate_total_nutrition(food_list)
    
    # BMR과 칼로리 요구량 계산 (사용자 정보 입력)
    user_info = {
        'weight': 70,  # kg
        'height': 175,  # cm
        'age': 30,  # 나이
        'gender': 'male',  # 성별
        'activity_level': 'active'  # 활동 수준
    }
    
    bmr = calculate_bmr(user_info['weight'], user_info['height'], user_info['age'], user_info['gender'])
    daily_calories = calculate_daily_calories(bmr, user_info['activity_level'])

    # GPT에 질문할 프롬프트 생성
    prompt = (f"사용자가 '{', '.join(food_list)}'을(를) 먹고 싶어합니다. "
              f"총 섭취 칼로리는 {total_intake['calories']}kcal이며, 하루 권장 칼로리는 {daily_calories}kcal입니다. "
              "이를 기반으로 적절한 운동과 식단 조정을 추천해 주세요.")
    
    # GPT 응답 받기
    gpt_response, _ = ask_chatgpt(prompt)
    
    # 결과 출력
    st.subheader("GPT 추천 피드백")
    st.write(gpt_response)

# 필요한 함수들 정의

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

def calculate_total_nutrition(food_list):
    total_nutrition = {'calories': 0, 'carbs': 0, 'protein': 0, 'fats': 0}
    for food in food_list:
        nutrition = get_nutrition_from_api(food)
        if isinstance(nutrition, dict):  # 올바른 영양 정보가 반환된 경우에만 합산
            for key in total_nutrition:
                total_nutrition[key] += nutrition.get(key, 0)
    return total_nutrition

def get_nutrition_from_api(food_item):
    api_url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": "5fbb52ae",  # Nutritionix App ID
        "x-app-key": "a0d7d77cc3991149fa147c5fd422d278",  # Nutritionix API Key
        "Content-Type": "application/json"
    }
    data = {"query": food_item}
    response = requests.post(api_url, headers=headers, json=data)
    response.raise_for_status()
    nutrients = response.json()['foods'][0]
    return {
        'calories': nutrients['nf_calories'],
        'carbs': nutrients['nf_total_carbohydrate'],
        'protein': nutrients['nf_protein'],
        'fats': nutrients['nf_total_fat']
    }

def ask_chatgpt(prompt):
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",  # 사용하고자 하는 OpenAI 모델
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    content = response.json()
    return content['choices'][0]['message']['content'].strip(), prompt
