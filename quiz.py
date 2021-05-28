#!/usr/bin/env python3

class Quiz(object):

    def __init__(self, name):
        self.questions = []

        with open(name) as file:
            for line in file:
                question = tuple(string.strip() for string in tuple(line.split("    ")))
                self.questions.append(question)
