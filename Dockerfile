FROM python:3.8-slim

WORKDIR /bot

COPY requirements.txt .

RUN pip install -r requirements.txt

EXPOSE 443 50000-65535

ADD DemonOverlord /bot/DemonOverlord
COPY run.py /bot

CMD ["python3.8", "run.py", "--dev"]