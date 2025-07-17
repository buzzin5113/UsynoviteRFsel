#/bin/bash
cd /opt/UsynoviteRFselenium
docker build -t usynoviterfsel .
docker run --network="host" --rm -v /opt/UsynoviteRFselenium:/app usynoviterfsel:latest 
