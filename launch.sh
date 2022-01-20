#!/bin/sh

docker run -d --env-file .env --mount src=/home/christoph/QuizBot/quizes,target=/quiz,type=bind registry.gitlab.com/churl/quizbot
