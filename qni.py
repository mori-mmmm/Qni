# -*- coding: utf-8 -*-
import discord
from discord.ext import tasks
import os

import openai
from openai import OpenAI

import asyncio

from paper_test import proc_paper_pdf

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

async def gpt_res_given_messages(model, messages):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content

async def gpt_res(model, prompt):
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return response.choices[0].message.content



BOT_PREFIX = '큐니야'

GUILD_ID = 1111111111111111111
GUILD_ID_list = [GUILD_ID]

class QniChan(discord.Client):
    def __init__(self, intents):
        super(QniChan, self).__init__(intents=intents)
        

    async def on_ready(self):
        await self.change_presence(status=discord.Status.online, activity=discord.Game("?"))

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.guild.id not in GUILD_ID_list:
            return

        if message.attachments:
            pass
        else:
            in_msg = message.content
            if in_msg.startswith(BOT_PREFIX):
                asyncio.create_task(self.on_message_handler(message, in_msg, message.channel))
    
    async def on_message_handler(self, message, in_msg, channel):
        if 'https://arxiv.org/abs/' in in_msg:
            url = 'https://arxiv.org/abs/' + in_msg.split('https://arxiv.org/abs/')[1][:10]
            self.messages = await proc_paper_pdf(url, channel)
        elif 'https://arxiv.org/pdf/' in in_msg:
            url = 'https://arxiv.org/abs/' + in_msg.split('https://arxiv.org/pdf/')[1][:10]
            self.messages = await proc_paper_pdf(url, channel)
        else:
            query = in_msg
            self.messages += [{
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                ],
            }]
            response = client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=self.messages,
                max_tokens=16384,
            )
            ret = response.choices[0].message.content
            await channel.send(ret)
            self.messages += [{
                "role": "assistant",
                "content": [
                    {"type": "text", "text": ret},
                ],
            }]



intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
discord_client = QniChan(intents=intents)
discord_client.run(TOKEN)
            

