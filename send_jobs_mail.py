# 파일명: send_jobs_mail.py

import os
import smtplib
import requests
import json
from email.message import EmailMessage

# 1. 설정 파일(config.json) 읽기
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

RECIPIENT_EMAIL = config['recipient_email']
SEARCH_KEYWORD = config['search_keyword']

# 2. GitHub Secrets에서 이메일 계정 정보 가져오기 (가장 중요!)
SENDER_EMAIL = os.environ.get('GMAIL_ADDRESS')
SENDER_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')

if not SENDER_EMAIL or not SENDER_PASSWORD:
    raise ValueError("GMAIL_ADDRESS 또는 GMAIL_APP_PASSWORD 환경변수가 설정되지 않았습니다.")

# 3. 원티드 API에서 채용 공고 데이터 가져오기
def fetch_wanted_jobs(keyword):
    """지정된 키워드로 원티드에서 채용 공고를 검색합니다."""
    url = f"https://www.wanted.co.kr/api/v4/jobs?country=kr&sort=job.latest_order&limit=5&query={keyword}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 오류가 발생하면 예외를 발생시킴
        jobs = response.json().get('data', [])
        return jobs
    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
        return []

# 4. 이메일 본문 생성
def create_email_body(jobs, keyword):
    """채용 공고 리스트로 이메일 HTML 본문을 만듭니다."""
    if not jobs:
        return f"'{keyword}' 키워드에 대한 새로운 채용 공고가 없습니다."

    body = f"<h2>'{keyword}' 최신 채용 공고 (상위 5개)</h2>"
    body += "<ul>"
    for job in jobs:
        position = job.get('position')
        company_name = job['company'].get('name')
        link = f"https://www.wanted.co.kr/wd/{job.get('id')}"
        body += f"<li><a href='{link}'><b>{position}</b> - {company_name}</a></li>"
    body += "</ul>"
    return body

# 5. 이메일 발송
def send_email(subject, body, recipient):
    """생성된 본문으로 이메일을 발송합니다."""
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient
    msg.set_content(body, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print(f"성공적으로 이메일을 발송했습니다: {recipient}")
    except Exception as e:
        print(f"이메일 발송 중 오류 발생: {e}")

# --- 스크립트 실행 ---
if __name__ == "__main__":
    print(f"'{SEARCH_KEYWORD}' 키워드로 채용 공고 검색을 시작합니다...")
    fetched_jobs = fetch_wanted_jobs(SEARCH_KEYWORD)
    
    email_subject = f"[{SEARCH_KEYWORD}] 새로운 채용 공고 알림"
    email_body = create_email_body(fetched_jobs, SEARCH_KEYWORD)
    
    send_email(email_subject, email_body, RECIPIENT_EMAIL)
