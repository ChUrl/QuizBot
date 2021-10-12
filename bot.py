#!/usr/bin/env python3
import asyncio
import os
import random
import re

import discord
from discord.message import Message
from dotenv import load_dotenv

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

        self.matchers = {"hilfe$": self.help,
                         "init: .*": self.init_quiz,
                         "start$": self.run_quiz,
                         "reset$": self.reset_quiz,
                         "scores$": self.show_scores,
                         "players$": self.show_players}

        # Voicelines

    # Events -------------------------------------------------------------------------------------

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

    # Helpers ------------------------------------------------------------------------------------

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

    def _reset(self):
        """
        Set the saved state to None
        """
        self.quiz = None
        self.channel = None
        self.quizmaster = None
        self.players = dict()
        self.scores = list()

    def _is_init(self):
        """
        Check if required state is present to start quiz/get scores etc
        """
        return not (self.quiz is None or
                    self.channel is None or
                    self.quizmaster is None or
                    self.players == dict())  # TODO: Include players here?

    async def _quizmaster_confirm(self, message):
        """
        Adds checkmark to message and waits for quizmaster reaction.
        Returns the newly fetched message
        """
        await message.add_reaction("✅")

        def check_confirm_players(reaction, user):
            return reaction.message == message and str(reaction.emoji) == "✅" and user == self.quizmaster

        await self.wait_for("reaction_add", check=check_confirm_players)
        react_message = discord.utils.get(client.cached_messages, id=message.id)
        assert isinstance(react_message, Message), "This should be a Message!"  # silence pyright
        return react_message

    async def _determine_players(self):
        # Players react to this message
        react_message = await self.channel.send(
            "Hier mit individuellem Emoji reagieren, am Ende mit dem Haken bestätigen!")
        react_message = await self._quizmaster_confirm(react_message)

        # Get players from emojis
        players = {}
        for reaction in react_message.reactions:
            if reaction.emoji == "✅":
                continue

            async for user in reaction.users():
                # if user == self.quizmaster:
                #     continue

                players[reaction.emoji] = user  # TODO: key value which order?

        return players

    async def _wait_for_players(self):
        def make_player_check(player):
            return lambda message: message.author == player

        await asyncio.wait(
            [asyncio.create_task(self.wait_for("message", check=make_player_check(p))) for p in self.players.values()])

    async def _message_players(self, message):
        await asyncio.wait([asyncio.create_task(p.send(message)) for p in self.players.values()])

    async def _ask_question(self, question):
        question_text, answer, embed = question
        await self._post_question_text(question_text, answer)
        await self._post_embed(embed)
        if isinstance(answer, tuple):
            await self._post_answer_choices(answer)
            return True

    async def _post_question_text(self, question, answer):
        await self.channel.send("**Frage:** " + question)

        if not isinstance(answer, tuple):
            await self._message_players("**Frage:** " + question)

    async def _post_embed(self, embed):
        if len(embed) < 2:
            return

        if embed[0] == "Image":
            picture = discord.Embed()
            picture.set_image(url=embed[1])
            await self.channel.send(embed=picture)
        elif embed[0] == "Video":
            await self.channel.send(embed[1])
        elif embed[0] == "Audio":
            await self.channel.send("Audio not implemented!")

    async def _post_answer_choices(self, choices):
        """
        Posts the answers in random order, returns the correct message
        """
        choices_rand = list(choices)
        await self.channel.send("Antwortmöglichkeiten:")
        while len(choices_rand) > 0:
            choice = random.choice(choices_rand)
            choices_rand.remove(choice)
            await self.channel.send("- " + choice)

    async def _post_answer(self, question):
        question, answer, embed = question

        if isinstance(answer, tuple):
            return await self.channel.send("**Korrekte Antwort:** " + answer[0])

        return await self.channel.send("**Korrekte Antwort:** " + answer)

    async def _fetch_reactants(self, message):
        turn_scores = list()
        for reaction in message.reactions:
            if reaction.emoji == "✅":
                continue

            async for user in reaction.users():
                if user != self.quizmaster:
                    continue

                turn_scores.append(reaction.emoji)

        return turn_scores

    # Commands -----------------------------------------------------------------------------------

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
        self._reset()
        await message.channel.send("Finished.")

    async def init_quiz(self, message):
        """
        Quiz, init: [NAME] - Initialisiere ein neues Quiz.
        """
        self._reset()  # Reset to enable multiple inits

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
        self.players = await self._determine_players()

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
        if not self._is_init():
            await message.channel.send("Vorher init du kek")
            return

        if not message.author == self.quizmaster:
            await self.channel.send("Kein QuizMaster, kein Quiz!")
            return

        # Run questions
        for question in self.quiz:
            multiple_choice = await self._ask_question(question)
            if not multiple_choice:
                await self._wait_for_players()  # TODO: If this makes problems replace this with manual quizmaster emoji
                cmsg = await self.channel.send("Alle Spieler haben geantwortet, fortfahren?")
            else:
                cmsg = await self.channel.send("Fortfahren?")
            await self._quizmaster_confirm(cmsg)
            await self.channel.send("- " * 40)

            # Antworten
            if not multiple_choice:
                await self.channel.send("**Antworten:**")
                for emoji, player in self.players.items():
                    await self.channel.send(
                        str(emoji) + ": " + str((await player.dm_channel.history(limit=1).flatten())[0].content))

            # Correct answer and scores
            amsg = await self._post_answer(question)
            for emoji, player in self.players.items():
                await amsg.add_reaction(emoji)
            amsg = await self._quizmaster_confirm(amsg)
            turn_scores = await self._fetch_reactants(amsg)
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
        if not self._is_init():
            await message.channel.send("Vorher init du kek")
            return

        if not message.author == self.quizmaster:
            await self.channel.send("Kein QuizMaster keine Punkte!")
            return

        # scores: [[A, B], [A], [B, C], ...]
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
        if not self._is_init():
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
