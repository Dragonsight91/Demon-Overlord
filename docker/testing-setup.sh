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

echo "creating directories"
mkdir  ~/bot ~/bot/db-data
cp docker-compose-testing.yaml ~/bot/docker-compose.yaml

docker build -f ./Dockerfile-testing -t demonoverlord:testing ..