#!/bin/sh

docker pull registry.gitlab.com/churl/quizbot
docker container rm -f quizbot
docker run -d --env-file /home/christoph/quizbot/.env --mount src=/home/christoph/quizbot/quizes,target=/quiz,type=bind --name quizbot registry.gitlab.com/churl/quizbot
