#!/usr/bin/env python3

import os
import re
from discord.message import Message
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
        self.quizmaster = None
        self.players = dict()
        self.scores = list()

        self.triggers = {}  # automatic actions
        # Example: self.triggers[lambda m: "jeremy" in m.author.nick.lower()] = self.autoreact_to_jeremy

        self.matchers = {}  # react to messages
        self.matchers["hilfe$"] = self.help
        self.matchers["init: .*"] = self.init_quiz
        self.matchers["start$"] = self.run_quiz
        self.matchers["reset$"] = self.reset_quiz
        self.matchers["scores$"] = self.show_scores
        self.matchers["players$"] = self.show_players

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

    async def help(self, message):
        """
        Quiz, hilfe - Hilfetext anzeigen
        """
        await message.channel.send(self._help_text())


    async def reset_quiz(self, message):
        """
        Quiz, reset - Gesetzte Werte zurücksetzen (zum neu Initialisieren)
        """
        await message.channel.send("Resetting...")

        self.quiz = None
        self.channel = None
        self.quizmaster = None
        self.players = dict()
        self.scores = list()

        await message.channel.send("Finished.")


    def is_init(self):
        return not (self.quiz == None or
                    self.channel == None or
                    self.quizmaster == None or
                    self.players == dict())


    async def init_quiz(self, message):
        """
        Quiz, init: [NAME] - Initialisiere ein neues Quiz.
        """

        # Reset to enable multiple inits
        await self.reset_quiz(message)

        # Set self.channel
        if "quiz" not in message.channel.name.lower():
            await message.channel.send("Kein Quizchannel mann!")
            return
        self.channel = message.channel

        # Set self.quizmaster
        if message.author.top_role.name != "QuizMaster":
            await self.channel.send("Nur für QuizMaster ey!")
            return
        self.quizmaster = message.author

        # Set self.quiz
        try:
            self.quiz = Quiz((message.content.split(": "))[1])
        except:
            await self.channel.send("Hab das Quiz nicht gefunden")
            return

        # Set self.players
        await self.channel.send("Determining players:")
        react_message = await self.channel.send("Hier mit individuellem Emoji reagieren, am Ende mit dem Haken bestätigen!")
        await react_message.add_reaction("✅")

        def check_confirm_players(reaction, user):
            return reaction.message == react_message and str(reaction.emoji) == "✅" and user == self.quizmaster

        await self.wait_for("reaction_add", check=check_confirm_players)
        react_message = discord.utils.get(client.cached_messages, id=react_message.id)
        assert isinstance(react_message, Message), "This should be a Message!" # silence pyright

        # Get players from emojis
        for reaction in react_message.reactions:
            if reaction.emoji == "✅":
                continue

            async for user in reaction.users():
                if user == self.quizmaster:
                    continue

                self.players[reaction.emoji] = user # TODO: key value which order?

        # Send starting message
        await self.channel.send("Quiz will start in channel \"" + self.channel.name + "\"")
        await self.channel.send("Players:")
        for emoji, player in self.players.items():
            await self.channel.send(str(emoji) + ": " + str(player.display_name))
        await self.channel.send("-" * 80)


    async def run_quiz(self, message):
        """
        Quiz, run - Starte das Quiz
        """
        if not self.is_init():
            await message.channel.send("Vorher init du kek")
            return

        if not message.author == self.quizmaster:
            await self.channel.send("Kein QuizMaster kein Quiz!")
            return

        for question, answer in self.quiz:

            # post question to players
            for player in self.players.values():
                await player.send("Frage: **" + question + "**")

            # post question to channel for confirmation
            await self.channel.send("Frage: **" + question + "**")

            # wait for answers from all players
            for player in self.players.values():
                def check_answers_given(message):
                    return message.author == player

                await self.wait_for("message", check=check_answers_given)

            # wait for confirmation
            cmsg = await self.channel.send("Alle Spieler haben geantwortet, fortfahren?")
            await cmsg.add_reaction("✅")

            def check_question_finished(reaction, user):
                return reaction.message == cmsg and str(reaction.emoji) == "✅" and user == self.quizmaster

            await self.wait_for("reaction_add", check=check_question_finished)
            await self.channel.send("- " * 40)

            # Antworten
            await self.channel.send("**Antworten:**")
            for emoji, player in self.players.items():
                await self.channel.send(str(emoji) + ": " + str((await player.dm_channel.history(limit=1).flatten())[0].content))

            amsg = await self.channel.send("Korrekte Antwort: " + answer)
            await amsg.add_reaction("✅")
            for emoji, player in self.players.items():
                await amsg.add_reaction(emoji)

            # Set Points
            def check_confirm_points(reaction, user):
                return reaction.message == amsg and str(reaction.emoji) == "✅" and user == self.quizmaster

            await self.wait_for("reaction_add", check=check_confirm_points)
            amsg = discord.utils.get(client.cached_messages, id=amsg.id)
            assert isinstance(amsg, Message), "This should be a Message!" # silence pyright

            turn_scores = list()
            for reaction in amsg.reactions:
                if reaction.emoji == "✅":
                    continue

                async for user in reaction.users():
                    if user != self.quizmaster:
                        continue

                    turn_scores.append(reaction.emoji)

            self.scores.append(turn_scores)

            # Separators at the end
            await self.channel.send("-" * 80)
            for player in self.players.values():
                await player.send("-" * 80)

        await self.channel.send("Quiz vorbei!")


    async def show_scores(self, message):
        """
        Quiz, scores - Zeigt den aktuellen Punktestand
        """
        if not self.is_init():
            await message.channel.send("Vorher init du kek")
            return

        if not message.author == self.quizmaster:
            await self.channel.send("Kein QuizMaster keine Punkte!")
            return

        # scores = [[A, B], [A], [B, C], ...]
        flat_scores = [player for round in self.scores for player in round]
        score_dict = dict()
        for emoji, _ in self.players.items():
            score_dict[emoji] = len(list(filter(lambda x: x == emoji, flat_scores)))

        await self.channel.send("Punktestand:")
        for emoji, score in sorted(score_dict.items(), key=lambda item: item[1]):
            await self.channel.send(str(emoji) + ": " + str(score) + " Punkte")


    async def show_players(self, message):
        """
        Quiz, players - Zeigt die Spielerliste
        """
        if not self.is_init():
            await message.channel.send("Vorher init du kek")
            return

        if not message.author == self.quizmaster:
            await self.channel.send("Kein QuizMaster keine Punkte!")
            return

        await self.channel.send("Players:")
        for emoji, player in self.players.items():
            await self.channel.send(str(emoji) + ": " + str(player.display_name))

client = QuizClient()
client.run(TOKEN)
