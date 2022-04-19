#!/bin/bash
# Taken from: https://gist.github.com/patrickfuller/08d3dffec086845d3a3249629677ffce#file-alias_dns-py

set -e # exit on any error

if [ ! -f /root/.ssh/id_rsa ]; then
  ssh-keygen -f /root/.ssh/id_rsa -q -N ""
  ssh-copy-id $USER@$HOST
fi

# RUN echo "* * * * * /usr/bin/python /usr/lib/unifi/alias_dns.py" >> /path/to/crontab
# service cron start

# Run, wait, repeat...
if [ "$1" = "" ]; then
  echo "Running default entry point."
  while true
  do
    exec python3 "$SCRIPT"
    sleep 60
  done
else
  exec "$@" # This runs any other cmd without starting service.
fi