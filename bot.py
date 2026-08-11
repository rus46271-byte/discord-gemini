import os
import discord
from google import genai

# 구글 제미나이 클라이언트 설정
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 디스코드 봇 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)


@discord_client.event
async def on_message(message):
  # 봇 자신이 보낸 메시지는 무시
  if message.author == discord_client.user:
    return

  # 느낌표(!)로 시작하기만 하면 띄어쓰기 없이도 작동
  if message.content.startswith("!"):
    user_message = message.content[1:].strip()

    try:
      # 제미나이 모델 호출 및 소녀 페르소나 설정
      prompt = (
          "너는 디스코드에 사는 제미나이 ai 야"
          + user_message
      )

      response = client.models.generate_content(
          model="gemini-2.5-flash", contents=prompt
      )

      await message.channel.send(response.text)

    except Exception as e:
      await message.channel.send(f"오류가 발생했어요: {e}")


# 봇 실행
discord_client.run(os.environ.get("DISCORD_TOKEN"))