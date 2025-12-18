#!/usr/bin/env bash

# only used for first-time initialization development

pwd=$(pwd)
folders=("$pwd/01-bulker-app" "$pwd/02-updater-app")

for folder in "${folders[@]}"; do
    cd $folder
    npm install
done