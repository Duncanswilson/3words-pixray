#make sure docker is loaded
docker -v

if ($==0)
then
  #install cog
  sudo curl -o /usr/local/bin/cog -L https://github.com/replicate/cog/releases/latest/download/cog_`uname -s`_`uname -m`
  sudo chmod +x /usr/local/bin/cog
fi

cog run python pixray.py --drawer=pixel --prompt= $2 $3 $4 --output $1.png
