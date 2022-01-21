#!/bin/sh

docker pull registry.gitlab.com/churl/quizbot
docker container rm -f quizbot
docker run -d --env-file .env --mount src=/home/christoph/QuizBot/quizes,target=/quiz,type=bind --name quizbot registry.gitlab.com/churl/quizbot
