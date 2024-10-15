# Qni 큐니: 한국어 논문 요약 및 Q&amp;A 디스코드 챗봇
Arxiv 논문 url을 입력하면 논문 내용을 요약하고, 이후 해당 논문에 대해 질문하면 관련 내용에 대해 답해줍니다.  
논문을 읽을지 말지 빠르게 결정하고 싶거나 논문에서 핵심이나 궁금한 내용만 먼저 알고 싶은 경우 유용합니다.

## 주의
LLM 특유의 hallucination 위험성이 있습니다. 중요한 내용은 직접 확인하세요.

## 예시
### ex1) Differential Transformer
![image](https://github.com/user-attachments/assets/633829c5-34a6-4251-9abc-f6987b95a792)
![image](https://github.com/user-attachments/assets/b6cb8940-6032-4ca6-8ba7-3008412b4604)

### ex2) LoLCATs
![image](https://github.com/user-attachments/assets/65e74c18-be07-490e-9403-8f48cf0acca8)


## 사용법
### python 패키지 설치
```
pip install -r requirements.txt
```

### .env 파일 설정
```
OPENAI_API_KEY="오픈AI API 키"
DISCORD_TOKEN="디스코드 봇 토큰"
```

### GUILD_ID 설정
봇의 작동을 허용할 디스코드 서버의 id  
`qni.py`의 GUILD_ID 값으로 설정 (1111111111111111111 부분)


## 사용문의
봇 서버를 운영할 환경이 여의치 않거나 이미 만들어진 봇을 서버에 초대해 사용하고 싶으신 경우 https://github.com/mori-mmmm 프로필의 메일 주소로 연락해주세요. 
