FROM python:3.8-slim

WORKDIR /bot

COPY requirements.txt .

RUN apt-get update
RUN apt-get install build-essential libpq-dev python3-dev git -yq
RUN pip install -r requirements.txt
RUN git clone https://github.com/Rapptz/discord.py.git
RUN cd discord.py; pip install .

EXPOSE 443 50000-65535

ADD ./DemonOverlord /bot/DemonOverlord
COPY ./run.py /bot/run.py

CMD ["python3.8", "-u", "run.py", "--prod"]