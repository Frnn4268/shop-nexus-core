#!/bin/sh

# Usage: ./wait-for.sh host:port [command] [timeout]
# Ejemplo: ./wait-for.sh db:27017 -- echo "MongoDB está listo"

set -e

host=$(echo $1 | cut -d : -f 1)
port=$(echo $1 | cut -d : -f 2)
shift
cmd="$@"
timeout=${TIMEOUT:-60}

start_ts=$(date +%s)
while :
do
    (echo > /dev/tcp/$host/$port) >/dev/null 2>&1
    result=$?
    if [[ $result -eq 0 ]]; then
        end_ts=$(date +%s)
        echo "Servicio $host:$port disponible después $((end_ts - start_ts)) segundos"
        exec $cmd
        exit 0
    fi
    echo "Esperando $host:$port..."
    sleep 1
    
    if [ $(( $(date +%s) - start_ts )) -gt $timeout ]; then
        echo "Timeout alcanzado ($timeout segundos). Servicio no disponible."
        exit 1
    fi
done