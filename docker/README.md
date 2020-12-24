# Deploy or Test the bot

This directory holds all files to deploy the bot on a server.

## Prerequisites

BEFORE you do ANYTHING with these files, you will have to install Docker and Docker compose:

- [Docker](https://docs.docker.com/get-docker/)

- [Docker Compose](https://docs.docker.com/compose/install/)

## Deployment

NOTE: **THIS SHOULD NEVER BE NECESSARY IF YOU ARE JUST DEVELOPING THE BOT !!!**

To really use the Docker containers, these envvars have to be set in `~/bot/bot.env`:

- `DISCORD_MAIN_TOKEN` (this is production only)
- `TENOR_TOKEN` (an api token for tenor)
- `POSTGRES_USER` (the postgres bot user)
- `POSTGRES_PASSWORD` (the password for the postgres bot user)
- `POSTGRES_SERVER` (the server address, e.g `localhost:5000`)
- `POSTGRES_PORT` (the port on `POSTGRES_SERVER` )
- `POSTGRES_DB` (The name of the bot database)

After that, just run `deploy-setup.sh` to set everything up for testing in `~/bot` (this is where all data will be saved) and then use 
`docker-compose --verbose -f /home/emma/bot/docker-compose.yaml up --detach --force-recreate --remove-orphans` 
to run the bot. run the same to restart the bot after making changes to the code.
