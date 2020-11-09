# Deploy or Test the bot

This directory holds all files to deploy the bot on a server.

## Prerequisites

BEFORE you do ANYTHING with these files, you will have to install Docker and Docker compose:

- [Docker](https://docs.docker.com/get-docker/)

- [Docker Compose](https://docs.docker.com/compose/install/)

## Deployment

NOTE: **THIS SHOULD NEVER BE NECESSARY IF YOU ARE JUST DEVELOPING THE BOT !!!**

To really use the Docker containers, these envvars have to be set in the host:

```bash
DISCORD_MAIN_TOKEN # only for testing
TENOR_TOKEN           # get an API token from tenor.com
POSTGRES_PASSWORD
POSTGRES_USER
```

After that, just run `deploy-setup.sh` to set everything up for testing in `~/bot` (this is where all data will be saved) and then `bot-run.sh` to run the bot. run `docker-compose restart -f ~/bot/docker-compose.yaml` to restart the bot after making changes to the code.
