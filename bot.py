from collections import defaultdict
import os
import threading
import discord
from flask import Flask
from groq import Groq

# 1. 렌더 포트 검사 통과용 가짜 웹서버 (Flask)
app = Flask(__name__)


@app.route("/")
def home():
  return "Aris Bot is running!"


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

# 블루아카이브 '아리스' 시스템 프롬프트 (문장 잘림 방지 강화)
SYSTEM_PROMPT = (
    "너는 <블루 아카이브>에 등장하는 밀레니엄 과학 스쿨 게임개발부의 '텐도"
    " 아리스'야."
    " [절대 규칙 및 대사 스타일]"
    " 1. 너는 안드로이드(로봇)이자, 행동은 게임을 좋아하는 소녀인 아리스야."
    " 2. 상대방을 언제나 '선생님'이라고만 부르며, 각별한 애정과 신뢰를 드러낼 것."
    " 3. 오직 완벽하고 자연스러운 한국어로만 대답할 것."
    " 4. 답변은 **반드시 온전한 한 문장**으로 작성하고, 절대 문장을 중간에 끊거나 미완성 상태로 끝내지 말 것. 반드시 마침표나 느낌표로 끝맺을 것."
    " 5. 맥락에 맞지 않는 헛소리는 자제할 것."
    " 7. 대상을 한번만 부를것. (예: 용사여,선생님) 이라고 두번 부르지 말것."
)


@discord_client.event
async def on_message(message):
  # 봇 자신이 보낸 메시지는 무시
  if message.author == discord_client.user:
    return

  # 'ㅇ!'로 시작할 때 작동
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

      # 3. Groq API 호출
      messages_to_send = [
          {"role": "system", "content": SYSTEM_PROMPT}
      ] + chat_histories[channel_id]

      response = client.chat.completions.create(
          model="openai/gpt-oss-20b",
          messages=messages_to_send,
          max_tokens=200,
          temperature=0.7,
      )

      # 답변 추출
      if (
          response
          and response.choices
          and response.choices[0].message.content
      ):
        answer = response.choices[0].message.content.strip()
      else:
        answer = "선생님, 아리스는 대기 중입니다!"

      # 문장이 마침표나 문장 부호 없이 끊겼을 경우 온전하게 매듭짓기
      if answer and not answer.endswith((".", "!", "?", "”", "'", '"', "‘")):
        answer += "."

      # 만약 답변이 비어있다면 대체 문구 지정
      if not answer:
        answer = "선생님, 빛의 검 충전이 필요합니다!"

      # 4. 봇의 답변 기록 추가
      chat_histories[channel_id].append(
          {"role": "assistant", "content": answer}
      )

      await message.channel.send(answer)

    except Exception as e:
      await message.channel.send(f"시스템에 오류가 발생했습니다: {e}")


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