The environment variables "DISCORD_TOKEN" and "DISCORD_GUILD" must be set to run the bot.
When run locally the boat loads an existing ".env"-file from the same directory as the script.
When running a docker container an ".env"-file can be loaded with "--env-file .env".

When run locally the quiz should be located in the same directory as the script.
When run from a docker container the folder containing the quiz should be mountet to "/quiz/" inside the container with "-v folder:/quiz".

docker run -d --env-file .env --mount src=/root/QuizBot/quizes,target=/quiz,type=bind registry.gitlab.com/churl/quizbot:latest
