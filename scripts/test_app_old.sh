#!/bin/sh

cleanup() {
    echo "CLEAN UP INVOKED"
}

APP_NAME=checkin_styler

SCRIPT_PATH=$(realpath "$0")
SCRIPT_FOLDER="${SCRIPT_PATH%/*}"
PROJECT_FOLDER="${SCRIPT_FOLDER%/*}"

cd $PROJECT_FOLDER

trap "cleanup()" TSTP

flask --app $APP_NAME run --debug &

wait
