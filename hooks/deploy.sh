#! /bin/bash

# Run Docker Compose
echo "Updating Docker Compose"
docker-compose pull
docker-compose up -d
