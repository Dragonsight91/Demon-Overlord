FROM python:3.8-slim

WORKDIR /bot

COPY requirements.txt .

RUN apt-get update
RUN apt-get install libpq-dev python3-dev -yq
RUN pip install -r requirements.txt

EXPOSE 443 50000-65535

ADD DemonOverlord /bot/DemonOverlord
COPY run.py /bot

CMD ["python3.8", "-u", "run.py", "--prod"]

# you will need additional envvars
