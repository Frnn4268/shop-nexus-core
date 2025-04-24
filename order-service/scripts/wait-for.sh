#!/bin/sh

set -e

host="$1"
shift
cmd="$@"

until nc -z $host 5672; do
  echo "Esperando a RabbitMQ en $host..."
  sleep 2
done

until nc -z mongo 27017; do
  echo "Esperando a MongoDB..."
  sleep 2
done

echo "Todos los servicios dependientes están listos!"
exec $cmd