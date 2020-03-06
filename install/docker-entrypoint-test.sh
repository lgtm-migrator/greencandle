#!/usr/bin/env bash

set -e

if [[ -z $CONFIG_ENV ]]; then
if [[ -z $CONFIG_ENV || -z $YEAR || -z $PAIR || -z $STRATEGY ]];
  echo "CONFIG_ENV var not set, exiting..."
  exit 1
fi

get_data()
$YEAR
$PAIR
$STRATEGY


if [[ ! -e /installed ]]; then
  configstore package process_templates --ignore-role --basedir /opt/config $CONFIG_ENV /opt/output
  cp /opt/output/greencandle.ini /etc/greencandle.ini || true
  touch /installed
fi

mysql=$(awk -F "=" '/db_host/ {print $2}' /etc/greencandle.ini)
redis=$(awk -F "=" '/redis_host/ {print $2}' /etc/greencandle.ini)

while ! nc -z $mysql 3306; do
  echo Waiting for mysql;
  sleep 1;
done

while ! nc -z $redis 6379; do
  echo Waiting for redis;
  sleep 1;
done

run_in_docker $YEAR $STRATEGY $PAIR
