#!/bin/bash

cog run python 3words_run.py --tokenID $1 --word1 $2 --word2 $3 --word3 $4

mv $1.json metadata/$1.json

mv $1.png image/$.png
sudo chmod -R 777 .git/objects
git add metadata/$1.json
git add image/$1.png
git add image-history/*.png
git add metadata-history/*.json
git commit -m "uploading new re-roll data for tokenID: $1"
git push origin master 

sudo poweroff
