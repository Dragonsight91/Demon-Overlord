FROM python:3.8-slim

WORKDIR /bot

COPY requirements.txt .

RUN apt-get update
RUN apt-get install libpq-dev python3-dev gcc -yq
RUN pip install -r requirements.txt

EXPOSE 443 50000-65535

VOLUME DemonOverlord /bot/DemonOverlord
VOLUME run.py /bot

CMD ["python3.8", "-u", "run.py", "--dev"]
