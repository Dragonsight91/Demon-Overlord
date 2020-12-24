#!/bin/bash
if $(which docker) -v; then
    echo "Docker is installed"
else
    echo "please install docker and docker compose first"
    exit 1
fi

if $(which docker-compose) -v; then
    echo "docker-compose is installed"
else
    echo "please install docker-compose first"
    exit 1
fi

echo "creating directories in ${HOME}/bot"
if [ ! -d "$HOME/bot" ]; then
    mkdir  $HOME/bot 
else
    echo "$HOME/bot already exists..." 
fi
if [ ! -d "$HOME/bot/registry" ]; then
    mkdir  $HOME/bot/registry 
else
    echo "$HOME/bot/registry already exists..." 
fi
if [ ! -d "$HOME/bot/database-data" ]; then
    mkdir  $HOME/bot/database-data 
else
    echo "$HOME/bot/database-data already exists..." 
fi

# only symlink the compose config so it is updated on pull
if [ -L $HOME/bot/docker-compose.yaml ] || [ -f $HOME/bot/docker-compose.yaml ]; then
    echo "docker-compose link already exists, replacing..."
    rm $HOME/bot/docker-compose.yaml
fi

if [ ! -f "$HOME/bot/bot.env" ]; then
    touch  $HOME/bot/bot.env
else
    echo "$HOME/bot/bot.env already exists..." 
fi

ln -s $PWD/docker-compose.yaml $HOME/bot/docker-compose.yaml

$(which docker) build -f $PWD/Dockerfile -t demonoverlord:latest ..



