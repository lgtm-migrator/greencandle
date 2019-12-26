# Testing & Build status

| Build  	| Status 	|
|----	|----	|
|Main image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/greencandle)](https://hub.docker.com/repository/docker/amrox/greencandle)	|
|Mysql image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/gc-mysql)](https://hub.docker.com/repository/docker/amrox/gc-mysql)	|
|Redis image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/gc-redis)](https://hub.docker.com/repository/docker/amrox/gc-redis)	|
|Webserver image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/webserver)](https://hub.docker.com/repository/docker/amrox/webserver)	|
|Dashboard image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/dashboard)](https://hub.docker.com/repository/docker/amrox/dashboard)	|
|Testing| [![Build Status](https://travis-ci.org/adiabuk/greencandle.svg?branch=master)](https://travis-ci.org/adiabuk/greencandle)|

# Releases

## 0.26
* Testing of docker instance functionality
* Combine API and GC into single image
* Log directly to journald with preserved severity
* More cleanup of wasted diskspace on host and containers
* Fix of engine using incomplete data to populate redis in live mode
* Release script to pull latest version tag and deploy
* Add AWS S3 fuse package to non-test server for backups and other data

## 0.25
* Add api for displaying current open trades with ability to sell
* Add local install to travis tests
* Fix Crontabs with dates in path
* Fix webserver reverse proxy paths
* General cleanup

## 0.24
* Fix paths for nginx reverse proxy
* Allow scipts to determine open trades
* Limit trades by time since previous trade
* Fix relaive path for image building


