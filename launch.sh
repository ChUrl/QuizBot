#!/bin/sh

cd /home/christoph/QuizBot
git pull

docker pull registry.gitlab.com/churl/quizbot
docker container rm -f quizbot
docker run -d --env-file /home/christoph/QuizBot/.env --mount src=/home/christoph/QuizBot/quizes,target=/quiz,type=bind --name quizbot registry.gitlab.com/churl/quizbot
docker image prune -f
