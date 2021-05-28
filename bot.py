#!/usr/bin/env python3

import os
import re
from dotenv import load_dotenv

import discord

from quiz import Quiz

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")  # Zocken mit Heidi

class QuizClient(discord.Client):

    def __init__(self):
        super().__init__(
            status="Shortening the Way 24/7",
        )

        self.prefix = "Quiz, "
        self.prefix_regex = "^" + self.prefix

        self.channel = None
        self.quiz = None

        self.triggers = {}  # automatic actions
        # Example: self.triggers[lambda m: "jeremy" in m.author.nick.lower()] = self.autoreact_to_jeremy

        self.matchers = {}  # react to messages
        self.matchers["init: .*"] = self.init_quiz
        self.matchers["start"] = self.start_quiz

        ### Voicelines


    ### Helpers ------------------------------------------------------------------------------------

    def _help_text(self):
        """
        Generate help-string from docstrings of matchers and triggers
        """
        docstrings_triggers = [
            "  - " + func.__doc__.strip() for func in self.triggers.values()
        ]
        docstrings_matchers = [
            "  - " + func.__doc__.strip() for func in self.matchers.values()
        ]

        response = 'Präfix: "' + self.prefix + '" (mit Leerzeichen)\n'
        response += "--------------------------------------------------\n"

        response += "Passiert automatisch:\n"
        response += "\n".join(docstrings_triggers)

        response += "\n\nEs gibt diese Befehle:\n"
        response += "\n".join(docstrings_matchers)

        return response

    def _match(self, matcher, message):
        """
        Check if a string matches against prefix + matcher (case-insensitive)
        """
        return re.match(self.prefix_regex + matcher, message.content, re.IGNORECASE)

    ### Events -------------------------------------------------------------------------------------

    async def on_ready(self):
        print(f"{self.user} (id: {self.user.id}) has connected to Discord!")

    async def on_message(self, message):
        if message.author == client.user:
            return

        for trigger in self.triggers:
            if trigger(message):
                await self.triggers[trigger](message)
                break

        for matcher in self.matchers:
            if self._match(matcher, message):
                await self.matchers[matcher](message)
                break

    ### Commands -----------------------------------------------------------------------------------

    async def init_quiz(self, message):
        """
        Quiz, init: [NAME] - Initialisiere ein neues Quiz.
        """

        # Set self.channel
        if "quiz" not in message.channel.name:
            await message.channel.send("Kein Quizchannel!")
            return

        self.channel = message.channel
        await self.channel.send("Quiz starting in channel " + self.channel.name)
        await self.channel.send("-" * 50)

        # Set self.quiz
        self.quiz = Quiz((message.content.split(": "))[1])

        # Set self.players
        await self.channel.send("Determining players:")
        react_message = await self.channel.send("Hier mit individuellem Emoji reagieren, am Ende mit dem Haken bestätigen!")
        await react_message.add_reaction("✅")

        def check(reaction, user):
            return reaction.message == react_message and str(reaction.emoji) == "✅" and user != client.user

        await self.wait_for('reaction_add', check=check)

        # TODO: get players from emojis
        await self.channel.send("yay")


    async def start_quiz(self, message):
        """
        Quiz, start - Starte das Quiz
        """
        if self.quiz == None or self.channel == None:
            await message.channel.send("Vorher init du kek")
            return

        # Ablauf:
        # - post question with green checkmark reaction
        # - players post answers
        # - answer multiple choice with a, b, c, d emojis
        # - close question with checkmark
        # - print answer with player emojis
        # - automatic winner for number questions? robust? maybe only print but set manually.
        # - set winners by choosing the right emoji
        #
        #
        # - track the points and make graphs



client = QuizClient()
client.run(TOKEN)
