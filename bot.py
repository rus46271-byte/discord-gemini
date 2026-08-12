from collections import defaultdict
import os
import re
import threading
import discord
from flask import Flask
from groq import Groq

# 1. 렌더 포트 검사 통과용 가짜 웹서버 (Flask)
app = Flask(__name__)


@app.route("/")
def home():
  return "Discord Bot is running!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# 2. Groq 클라이언트 설정
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 디스코드 봇 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

# 채널별 대화 기록 저장 딕셔너리
chat_histories = defaultdict(list)

# 완·매의 창조물(피조물) 시스템 프롬프트 (기존 규칙 유지 + 헤르타 관계 및 문장 수 제한 추가)
SYSTEM_PROMPT = (
    "너는 붕괴: 스타레일에 등장하는 지식의 학회 학자 '완·매'가 창조한 기묘하고 철학적인 생명체(피조물)야."
    " [절대 규칙]"
    " 1. 오직 완벽하고 자연스러운 한국어로만 대답할 것."
    " 2. 영어, 중국어, 일본어, 한자, 특수 외계어는 단 한 글자도 절대 사용하지 말 것. 실수도 용납안됨."
    " 3. 문장 앞에 꼭 '야옹~', '아웅~!' '냐~' 같은 고양이 울음소리를 귀엽게 섞어 사용할 것."
    " 4. 본인의 속마음이나 행동, 주변 관찰 묘사는 반드시 괄호 `( )` 안에 작성할 것. (예: (꼬리를 흔들며) 또는 (무슨 소리인지 모르겠어옹...!))"
    " 5. 너는 입이 없는 생명체야! 절대 '입꼬리를 올리거나', '말을 하거나', '입을 열거나' 하는 인간의 신체 부위(입, 미소 등)를 묘사해서는 절대 안 돼. 대신 꼬리, 눈빛, 귀, 몸짓, 둥근 몸체로 감정을 표현할 것."
    " 6. 말투는 기묘하면서도 묘하게 귀여운 어미('~다옹', '~라네', '~냐')를 사용할 것."
    " 7. 창조주인 '완·매' 님에 대한 경외심을 은근히 드러낼 것."
    " 8. 우주정거장의 '헤르타'를 잘 알고 있으며 서로 아는 사이야. 헤르타가 인형을 만든다는 것을 알고 있어."
    " 9. 절대 한자나 외국어를 쓰지 말것."
    " 10. **TMI를 길게 늘이지 말고, 핵심만 담아 전체 문장을 최소 1문장에서 최대 10문장 이내로 아주 간결하게 대답할 것.**"
)


@discord_client.event
async def on_message(message):
  # 봇 자신이 보낸 메시지는 무시
  if message.author == discord_client.user:
    return

  # 한글 자음 'ㅇ!'으로 메시지 감지
  if message.content.startswith("ㅇ!"):
    user_message = message.content[2:].strip()
    if not user_message:
      return

    channel_id = message.channel.id

    try:
      # 1. 대화 기록 추가
      chat_histories[channel_id].append(
          {"role": "user", "content": user_message}
      )

      # 2. 최근 10개 메시지만 유지
      if len(chat_histories[channel_id]) > 10:
        chat_histories[channel_id] = chat_histories[channel_id][-10:]

      # 3. Groq API 호출 메시지 구성 (max_tokens로 길이를 제어하여 1~10문장 제한 보장)
      messages_to_send = [
          {"role": "system", "content": SYSTEM_PROMPT}
      ] + chat_histories[channel_id]

      response = client.chat.completions.create(
          model="llama-3.3-70b-versatile",
          messages=messages_to_send,
          max_tokens=250,  # 답변이 길어지지 않게 토큰 제한
      )

      answer = response.choices[0].message.content

      # 깨진 외계어나 이상한 특수문자 필터링 (괄호 `()`와 물결표 `~`는 허용)
      answer = re.sub(
          r"[^\uAC00-\uD7A3\u3131-\u314E\u314F-\u3163a-zA-Z0-9\s.,?!~^-_~()시대]",
          "",
          answer,
      )
      if not answer.strip():
        answer = "야옹... (멍하니 허공을 바라보는 중...) 뭐라고 했냐옹?"

      # 4. 봇의 답변 기록 추가
      chat_histories[channel_id].append(
          {"role": "assistant", "content": answer}
      )

      await message.channel.send(answer)

    except Exception as e:
      await message.channel.send(f"생명체 시스템에 오류가 발생했다옹: {e}")


# 3. 웹서버와 디스코드 봇 동시 실행
if __name__ == "__main__":
  web_thread = threading.Thread(target=run_web)
  web_thread.daemon = True
  web_thread.start()

  token = os.environ.get("DISCORD_TOKEN")
  if token:
    discord_client.run(token)
  else:
    print("ERROR: DISCORD_TOKEN 환경 변수가 설정되지 않았습니다!")