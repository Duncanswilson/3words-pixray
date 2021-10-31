#!/bin/bash
#make sure docker is loaded
docker -v

if ($==0)
then
  #install cog
  sudo curl -o /usr/local/bin/cog -L https://github.com/replicate/cog/releases/latest/download/cog_`uname -s`_`uname -m`
  sudo chmod +x /usr/local/bin/cog
fi
prompt = "$2 $3 $4"
cog run python pixray.py --drawer=pixel --prompt prompt --output $1.png
sudo poweroff
