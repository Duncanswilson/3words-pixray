#!/bin/bash

#install cog
sudo curl -o /usr/local/bin/cog -L https://github.com/replicate/cog/releases/latest/download/cog_`uname -s`_`uname -m`
  sudo chmod +x /usr/local/bin/cog


tmux new-session -d -s my_session "./generation.sh $1 $2 $3 $4  2>&1 | tee log.txt"
