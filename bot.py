import os
import time
import discord
from google import genai
from google.genai import errors

# 구글 제미나이 클라이언트 설정
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 사용할 모델 (문제가 잦은 2.5-flash 대신 최신 안정 모델 사용)
MODEL_NAME = "gemini-3.5-flash"

# 디스코드 봇 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

@discord_client.event
async def on_message(message):
    # 봇 자신이 보낸 메시지는 무시
    if message.author == discord_client.user:
        return

    # 마침표(.)로 시작하기만 하면 뒤에 띄어쓰기 없이도 작동
    if message.content.startswith("."):
        user_message = message.content[1:].strip()
        if not user_message:
            return

        # 일시적인 404/서버 오류에 대비한 재시도 로직
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME, contents=user_message
                )
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