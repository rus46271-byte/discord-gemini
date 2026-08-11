from collections import defaultdict
import os
import time
import discord
from google import genai
from google.genai import errors

# 구글 제미나이 클라이언트 설정
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 사용할 모델 (최신 안정 모델)
MODEL_NAME = "gemini-3.5-flash"

# 디스코드 봇 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

# 채널별로 대화 세션을 저장할 딕셔너리
# 제미나이 SDK의 chats 기능을 활용하여 대화 맥락을 유지합니다.
channel_chats = {}


@discord_client.event
async def on_message(message):
  # 봇 자신이 보낸 메시지는 무한 루프 방지를 위해 반드시 무시해야 합니다!
  if message.author == discord_client.user:
    return

  # 마침표(.)로 시작하기만 하면 작동
  if message.content.startswith("."):
    user_message = message.content[1:].strip()
    if not user_message:
      return

    channel_id = message.channel.id

    # 1. 해당 채널의 채팅 세션이 없으면 새로 생성 (이전 대화 기억 시작점)
    if channel_id not in channel_chats:
      channel_chats[channel_id] = client.chats.create(model=MODEL_NAME)

    chat_session = channel_chats[channel_id]

    # 일시적인 404/서버 오류에 대비한 재시도 로직
    max_retries = 2
    for attempt in range(max_retries + 1):
      try:
        # 2. 기존 대화 맥락과 함께 메시지 전송
        response = chat_session.send_message(user_message)
        await message.channel.send(response.text)
        break
      except errors.APIError as e:
        if attempt < max_retries:
          time.sleep(2)
          continue
        await message.channel.send(f"오류가 발생했어요: {e}")
      except Exception as e:
        await message.channel.send(f"오류가 발생했어요: {e}")
        break


# 봇 실행
discord_client.run(os.environ.get("DISCORD_TOKEN"))