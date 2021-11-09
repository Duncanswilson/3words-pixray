#!/bin/bash

#install cog
sudo curl -o /usr/local/bin/cog -L https://github.com/replicate/cog/releases/latest/download/cog_`uname -s`_`uname -m`
  sudo chmod +x /usr/local/bin/cog

prompt="$2 $3 $4"
echo $prompt

filename="$1.png"
echo $filename

tmux new-session -d -s my_session "cog run python pixray.py --drawer=pixel --prompt '$prompt' --output $filename  2>&1 | tee log.txt"
