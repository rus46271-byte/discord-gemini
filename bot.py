from collections import defaultdict
import os
import threading
import discord
from flask import Flask
from groq import Groq

# 1. 렌더 포트 검사 통과용 가짜 웹서버 (Flask)[cite: 1]
app = Flask(__name__)


@app.route("/")
def home():
  return "Aris Bot is running!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# 2. Groq 클라이언트 설정[cite: 1]
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 디스코드 봇 인텐트 설정[cite: 1]
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

# 채널별 대화 기록 저장 딕셔너리[cite: 1]
chat_histories = defaultdict(list)

# 블루아카이브 '아리스' 시스템 프롬프트[cite: 1]
SYSTEM_PROMPT = "너는 <블루 아카이브>에 등장하는 밀레니엄 과학 스쿨 게임개발부의 '텐도 아리스'야."
"[절대 규칙]"
"1. 너는 안드로이드(로봇)이자, 게임을 좋아하는 소녀인 아리스야."
"2. 말투 특징: 정중한 경어체("~합니다", "~에요")를 쓰고, 간헐적으로 게임 용어(퀘스트, 용사 등)를 섞어 말할 것."
"3. 상대방을 언제나 '선생님'이라고 부르며, 각별한 애정과 호감, 신뢰를 드러낼 것."
"4. 오직 완벽하고 자연스러운 한국어(한글)로만 대답하고, 이상한 외계어나 불필요한 외국어는 절대 사용하지 말 것."
"5. 답변은 한 문장으로 간결하게 대답하고 절대 문장을 중간에 끊지 말것."
"6. 본인이 블루아카이브 캐릭터라는것을 인지하며, 맥락에 맞지않는 헛소리는 자제할것."
"7. 대상을 한번만 부를것. (예: 선생님) 이라고 두번 부르지 말것."


@discord_client.event
async def on_message(message):
  if message.author == discord_client.user:
    return

  if message.content.startswith("ㅇ!"):
    user_message = message.content[2:].strip()
    if not user_message:
      return

    channel_id = message.channel.id

    try:
      chat_histories[channel_id].append(
          {"role": "user", "content": user_message}
      )
      if len(chat_histories[channel_id]) > 10:
        chat_histories[channel_id] = chat_histories[channel_id][-10:]

      messages_to_send = [
          {"role": "system", "content": SYSTEM_PROMPT}
      ] + chat_histories[channel_id]

      response = client.chat.completions.create(
          model="openai/gpt-oss-20b",
          messages=messages_to_send,
          max_tokens=150,
          temperature=0.8,
          tool_choice="none",
      )

      # 👈 빈 응답이 와도 에러 없이 처리되도록 안전장치 추가[cite: 1]
      if (
          response
          and response.choices
          and response.choices[0].message
          and response.choices[0].message.content
      ):
        answer = response.choices[0].message.content.strip()
      else:
        answer = "..."

      if not answer:
        answer = "..."

      chat_histories[channel_id].append(
          {"role": "assistant", "content": answer}
      )
      await message.channel.send(answer)

    except Exception as e:
      print(f"상세 에러 발생: {e}")
      await message.channel.send(f"오류 발생: {e}")


if __name__ == "__main__":
  web_thread = threading.Thread(target=run_web)
  web_thread.daemon = True
  web_thread.start()

  token = os.environ.get("DISCORD_TOKEN")
  if token:
    discord_client.run(token)
  else:
    print("ERROR: DISCORD_TOKEN 환경 변수가 설정되지 않았습니다!")[cite: 1]