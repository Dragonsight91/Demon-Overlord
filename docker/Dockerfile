FROM python:3.9.1-slim

WORKDIR /bot

# update python dev dependencies
RUN apt-get update
RUN apt-get install build-essential libpq-dev python3-dev git -yq

# get own dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# set up container
EXPOSE 443 50000-65535
ADD ./DemonOverlord /bot/DemonOverlord
COPY ./run.py /bot/run.py

# run the thing
CMD ["python3.8", "-u", "run.py", "--prod"]
