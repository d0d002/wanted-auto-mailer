# 파일명: send_jobs_mail.py

import os
import smtplib
import requests
import json
from email.message import EmailMessage
from urllib.parse import urlencode

# --- 1. 설정 및 환경 변수 불러오기 ---
try:
    # 설정 파일(config.json) 읽기
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    RECIPIENT_EMAIL = config['recipient_email']
    SEARCH_LOCATIONS = config['locations']
    SEARCH_YEAR = config['year']
    SEARCH_KEYWORD = config['jobs_keyword']

    # GitHub Secrets에서 이메일 계정 정보 가져오기
    SENDER_EMAIL = os.environ['GMAIL_ADDRESS']
    SENDER_PASSWORD = os.environ['GMAIL_APP_PASSWORD']

except KeyError as e:
    raise ValueError(f"필수 설정 또는 환경변수가 없습니다: {e}")


# --- 2. 원티드 API에서 채용 공고 데이터 가져오기 ---
def fetch_wanted_jobs():
    """설정된 조건으로 원티드에서 채용 공고를 검색합니다."""
    # API 파라미터를 동적으로 구성
    params = {
        'country': 'kr',
        'job_sort': 'job.latest_order',
        'limit': 10,  # 가져올 공고 수
        'years': SEARCH_YEAR,
        'query': SEARCH_KEYWORD,
    }
    
    # URL 쿼리 스트링 생성 (locations는 여러 개일 수 있으므로 별도 처리)
    query_string = urlencode(params, doseq=False)
    for location in SEARCH_LOCATIONS:
        query_string += f"&locations={location}"

    url = f"https://www.wanted.co.kr/api/v4/jobs?{query_string}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
        jobs = response.json().get('data', [])
        return jobs
    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
        return None

# --- 3. 이메일 본문 생성 ---
def create_email_body(jobs):
    """채용 공고 리스트로 이메일 HTML 본문을 만듭니다."""
    if not jobs:
        return f"요청하신 조건에 맞는 새로운 채용 공고가 없습니다."

    # 검색 조건을 이메일 제목 아래에 명시
    search_conditions = f"<b>지역:</b> {', '.join(SEARCH_LOCATIONS)} | <b>경력:</b> {SEARCH_YEAR}년차 | <b>키워드:</b> {SEARCH_KEYWORD}"
    
    body = f"<h2>요청하신 조건의 최신 채용 공고입니다</h2>"
    body += f"<p>{search_conditions}</p><hr>"
    
    for job in jobs:
        position = job.get('position', 'N/A')
        company_name = job.get('company', {}).get('name', 'N/A')
        link = f"https://www.wanted.co.kr/wd/{job.get('id')}"
        location = job.get('address', {}).get('short_location', '정보 없음')
        
        body += f"""
        <div style="margin-bottom: 15px; padding: 10px; border: 1px solid #eee; border-radius: 5px;">
            <h4 style="margin: 0 0 5px 0;"><a href='{link}'>{position}</a></h4>
            <p style="margin: 0 0 5px 0;"><b>회사:</b> {company_name}</p>
            <p style="margin: 0; color: #555;"><b>지역:</b> {location}</p>
        </div>
        """
    return body

# --- 4. 이메일 발송 ---
def send_email(subject, body):
    """생성된 본문으로 이메일을 발송합니다."""
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg.set_content(body, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print(f"성공적으로 이메일을 발송했습니다: {RECIPIENT_EMAIL}")
    except Exception as e:
        print(f"이메일 발송 중 오류 발생: {e}")
        raise e

# --- 스크립트 실행 로직 ---
if __name__ == "__main__":
    print("채용 공고 검색을 시작합니다...")
    fetched_jobs = fetch_wanted_jobs()
    
    if fetched_jobs is not None:
        email_subject = f"[{SEARCH_KEYWORD}] 맞춤 채용 공고 알림"
        email_body = create_email_body(fetched_jobs)
        send_email(email_subject, email_body)
    else:
        print("API 요청 실패로 작업을 중단합니다.")