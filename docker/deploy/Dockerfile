FROM python:3.8-slim

WORKDIR /bot

COPY ../requirements.txt .

RUN pip install -r ../requirements.txt

EXPOSE 443 50000-65535

ADD ./DemonOverlord /bot/DemonOverlord
COPY ./run.py /bot

CMD ["python3.8", "-u", "run.py", "--prod"]

# you will need additional envvars
# DISCORD_MAIN_TOKEN
# DISCORD_TESTBOT_TOKEN
# TENOR_TOKEN
# POSTGRES_PASSWORD
# POSTGRES_USER
