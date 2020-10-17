if docker -v; then
    echo "Docker is installed"
else
    echo "please install docker and docker compose first"
    exit 1
fi

if docker-compose -v; then
    echo "docker-compose is installed"
else
    echo "please install docker-compose first"
    exit 1
fi

echo "creating directories in ${HOME}/bot"
mkdir  ~/bot ~/bot/registry ~/bot/db-data
cp ./deploy/docker-compose.yaml ~/bot/docker-compose.yaml

echo "starting registry"
docker run -d -p 5678:5000 -v `${PWD}`/bot/registry:/var/lib/registry --restart=always --name registry registry:2
echo "registry available on Port 5678"

docker build -f ./deploy/Dockerfile -t demonoverlord:latest ..
docker image tag demonoverlord:latest localhost:5678/demonoverlord
docker push localhost:5678/demonoverlord



