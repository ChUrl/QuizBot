#!/usr/bin/env python3

import os
from dotenv import load_dotenv

import discord

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")  # Zocken mit Heidi


class QuizClient(discord.Client):
    def __init__(self):
        super().__init__(
            status="Shortening the Way 24/7",
        )

        self.prefix = "Heidi, "

    ### Helpers ------------------------------------------------------------------------------------


    ### Events -------------------------------------------------------------------------------------

    async def on_ready(self):
        print(f"{self.user} (id: {self.user.id}) has connected to Discord!")

    async def on_message(self, message):
        if message.author == client.user:
            return

    ### Commands -----------------------------------------------------------------------------------


client = QuizClient()
client.run(TOKEN)
