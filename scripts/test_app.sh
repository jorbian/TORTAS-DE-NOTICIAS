#!/bin/sh

DEFAULT_APP_NAME=app

SCRIPT_PATH=$(realpath "$0")
SCRIPT_FOLDER="${SCRIPT_PATH%/*}"
PROJECT_FOLDER="${SCRIPT_FOLDER%/*}"

if [ -z "$1" ]; then
    APP_NAME=$DEFAULT_APP_NAME
else
    APP_NAME=$1
fi

APP_FOLDER="$PROJECT_FOLDER/$APP_NAME"

if [ ! -d "$APP_FOLDER" ]; then
  printf '%s: app folder "%s" does not exist\n' $0 $APP_FOLDER
  exit 1
fi

cd $PROJECT_FOLDER

flask --app $APP_NAME run --debug &
