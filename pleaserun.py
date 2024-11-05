import os
import streamlit as st
from google.cloud import translate_v2 as translate
import requests
import json
from gtts import gTTS
import base64

# TTS 함수 정의
def tts(response_text):
    filename = "output.mp3"
    tts = gTTS(text=response_text, lang="ko")
    tts.save(filename)

    # mp3 파일을 base64로 인코딩하여 Streamlit에 표시
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        audio_html = f"""
            <audio autoplay="True" controls>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)

    # 사용이 끝난 파일 삭제
    os.remove(filename)

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


#nutrition 음식목록 가져오기 함수
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
        nutrients = response.json().get('foods', [])
        
        # 음식 목록이 비어있을 경우
        if not nutrients:
            st.error(f"{food}는 아직 잇차가 분석할 수 없어요 😢 다른 음식을 시도해보시겠어요?")
            return None
        
        return {
            'calories': nutrients[0]['nf_calories'],
            'carbs': nutrients[0]['nf_total_carbohydrate'],
            'protein': nutrients[0]['nf_protein'],
            'fats': nutrients[0]['nf_total_fat']
        }
        
    except requests.exceptions.HTTPError as http_err:
        st.error("잇차가 실수했어요! 요청을 다시 보내주시겠어요?")
        return None
    except Exception as err:
        st.error(f"An error occurred: {err}")
        return None





# Streamlit UI 설정



# GitHub에 업로드된 이미지 URL
image_url = "https://github.com/ssuracle/nutrition-recommendation/blob/main/eatchabig2.jpg?raw=true"

# 이미지 삽입
#st.image(image_url, use_column_width=True)



st.title("누비랩 NUVILAB")
st.header("내 손 안의 헬스케어 시작 💪🏻")



# 사용자 정보 입력

# 키 입력 및 버튼
st.write("키를 선택하세요! (cm)")
if 'height' not in st.session_state:
    st.session_state['height'] = 160  # 기본값 설정

height = st.number_input("키 입력", min_value=140, max_value=180, step=1, value=st.session_state['height'])  # 기본값 설정

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("140 cm"):
        st.session_state['height'] = 140  # 세션 상태 업데이트
with col2:
    if st.button("150 cm"):
        st.session_state['height'] = 150  # 세션 상태 업데이트
with col3:
    if st.button("160 cm"):
        st.session_state['height'] = 160  # 세션 상태 업데이트
with col4:
    if st.button("170 cm"):
        st.session_state['height'] = 170  # 세션 상태 업데이트
with col5:
    if st.button("180 cm"):
        st.session_state['height'] = 180  # 세션 상태 업데이트

# 체중 입력 및 버튼
st.write("체중을 선택하세요! (kg)")
if 'weight' not in st.session_state:
    st.session_state['weight'] = 70  # 기본값 설정

weight = st.number_input("체중 입력", min_value=40, max_value=90, step=1, value=st.session_state['weight'])  # 기본값 설정

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("40 kg"):
        st.session_state['weight'] = 40  # 세션 상태 업데이트
with col2:
    if st.button("50 kg"):
        st.session_state['weight'] = 50  # 세션 상태 업데이트
with col3:
    if st.button("60 kg"):
        st.session_state['weight'] = 60  # 세션 상태 업데이트
with col4:
    if st.button("70 kg"):
        st.session_state['weight'] = 70  # 세션 상태 업데이트
with col5:
    if st.button("80 kg"):
        st.session_state['weight'] = 80  # 세션 상태 업데이트

# 나이 입력 및 버튼
st.write("나이를 선택하세요!")
if 'age' not in st.session_state:
    st.session_state['age'] = 30  # 기본값 설정

age = st.number_input("나이 입력", min_value=20, max_value=60, step=1, value=st.session_state['age'])  # 기본값 설정

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("20세"):
        st.session_state['age'] = 20  # 세션 상태 업데이트
with col2:
    if st.button("30세"):
        st.session_state['age'] = 30  # 세션 상태 업데이트
with col3:
    if st.button("40세"):
        st.session_state['age'] = 40  # 세션 상태 업데이트
with col4:
    if st.button("50세"):
        st.session_state['age'] = 50  # 세션 상태 업데이트
with col5:
    if st.button("60세"):
        st.session_state['age'] = 60  # 세션 상태 업데이트

# 각 입력 필드에 반영
height = st.session_state['height']
weight = st.session_state['weight']
age = st.session_state['age']




# 성별 선택 + 활동수준 선택
gender = st.radio("성별을 선택하세요!", options=["남성", "여성"])
activity_level = st.radio("활동 수준 정도를 선택하세요!", options=["낮음", "보통", "높음"])

# 음식 목록 입력
food_list = st.text_area("어떤 음식을 드시고 싶으신가요? 🍽️ (ex : 사과, 바나나)", "")

# 피드백이 생성되는지 확인하는 플래그
feedback_generated = False

if st.button("맞춤 피드백을 받아보시겠어요? 🧐"):
    if not food_list:
        st.warning("정보가 올바르게 입력되지 않았어요 😢")
    else:
        with st.spinner("맞춤 피드백 생성 중... 👩🏻‍💻"):
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
            prompt = (f"사용자가 '{food_list}'을(를) 먹고 싶어합니다. "
                      f"총 섭취 칼로리는 {total_nutrition['calories']:.2f}kcal이며, "
                      f"하루 권장 칼로리는 {daily_calories:.2f}kcal입니다. "
                      "당신은 사용자의 친절한 헬스 트레이너입니다. 이 정보들을 기반으로 적절한 운동과 대체 식단 옵션(양을 반만 먹어라, 저지방 재료로 대체해라 등)을 포함해 친절한 추천 피드백을 해주세요."
                      "식단은 한국 음식으로 추천해주면 좋고, 말투는 부드럽고 친절한 말투로 해주세요.")

            feedback = ask_chatgpt(prompt)

            # 피드백을 세션 상태에 저장
            st.session_state['feedback'] = feedback
            feedback_generated = True  # 피드백이 생성되었음을 표시

# 피드백이 세션 상태에 있거나 새로 생성되었을 경우 한 번만 출력
if 'feedback' in st.session_state and (feedback_generated or st.session_state['feedback']):
    st.subheader("맞춤 피드백이 생성되었습니다! 💁🏻‍♀️")
    st.markdown(st.session_state['feedback'])

    # 피드백을 음성으로 출력하는 버튼
    if st.button("맞춤 피드백을 음성으로도 들어볼까요? 🎧"):
        tts(st.session_state['feedback'])
        st.success("맞춤 피드백을 음성으로 들려드릴게요! 👌🏻")
