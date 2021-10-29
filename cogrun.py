import cog
from pathlib import Path
import torch
import pixray
import yaml
import pathlib
import os
import yaml
import boto3
from git import Repo
from git import Git

# https://stackoverflow.com/a/6587648/1010653
import tempfile, shutil
def create_temporary_copy(src_path):
    _, tf_suffix = os.path.splitext(src_path)
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"tempfile{tf_suffix}")
    shutil.copy2(src_path, temp_path)
    return temp_path

class BasePixrayPredictor(cog.Predictor):
    def setup(self):
        print("---> BasePixrayPredictor Setup")
        os.environ['TORCH_HOME'] = 'models/'
        

        # get the private key for the backend datastore
        ssm = boto3.client('ssm')
        parameter = ssm.get_parameter(Name='/github/g4_key')
        backend_private_key = parameter['Parameter']['Value']

        with open('g4_key', 'w') as outfile:
            outfile.write(private_key)
        os.chmod('g4_key', 0o600)
        git_ssh_identity_file = os.path.expanduser('g4_key')
        git_ssh_cmd = 'ssh -i %s' % git_ssh_identity_file
        if not exists(pixelNFTbackend):
            with Git().custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
                 Repo.clone_from('git@github.com:Duncanswilson/3words_test.git', '3words_test/', branch='main')

    # Define the input types for a prediction
    @cog.input("settings", type=str, help="Default settings to use")
    @cog.input("tokenID", type=str, help="TokenID")
    @cog.input("prompts", type=str, help="Text Prompts")
    def predict(self, settings, tokenID, **kwargs):
        """Run a single prediction on the model"""
        print("---> BasePixrayPredictor Predict")
        os.environ['TORCH_HOME'] = 'models/'
        settings_file = f"cogs/{settings}.yaml"
        with open(settings_file, 'r') as stream:
          try:
              base_settings = yaml.safe_load(stream)
          except yaml.YAMLError as exc:
              print("YAML ERROR", exc)
              sys.exit(1)

        pixray.reset_settings()
        pixray.add_settings(**base_settings)
        pixray.add_settings(**kwargs)
        pixray.add_settings(skip_args=True)
        #add name to output here 
        settings = pixray.apply_settings()
        pixray.do_init(settings)
        run_complete = False
        counter = 0 
        while run_complete == False:
            run_complete = pixray.do_run(settings, return_display=True)
            temp_copy = create_temporary_copy(settings.output)
            yield pathlib.Path(os.path.realpath(temp_copy))
            os.system("cp {}.png 3words_test/{}.png".format(tokenID, tokenID))
            os.system("cd 3words_test")
            os.system("git add {}.png".format(tokenID))
            os.system("git commit -m 'adding iteration {} of tokenID {}'".format(counter, tokenID))
            os.system("git push origin main")
            os.system("cd ..")
            count += 1

class PixrayVqgan(BasePixrayPredictor):
    @cog.input("prompts", type=str, help="text prompt", default="rainbow mountain")
    @cog.input("quality", type=str, help="better is slower", default="normal", options=["draft", "normal", "better", "best"])
    @cog.input("aspect", type=str, help="wide vs square", default="widescreen", options=["widescreen", "square"])
    # @cog.input("num_cuts", type=int, default="24", min=4, max=96)
    # @cog.input("batches", type=int, default="1", min=1, max=32)
    def predict(self, **kwargs):
        yield from super().predict(settings="pixray_vqgan", **kwargs)

class PixrayPixel(BasePixrayPredictor):
    
    @cog.input("prompts", type=str, help="text prompt", default="Beirut Skyline. #pixelart")
    @cog.input("aspect", type=str, help="wide vs square", default="square", options=["widescreen", "square"])
    @cog.input("drawer", type=str, help="render engine", default="pixel", options=["pixel", "vqgan", "line_sketch", "clipdraw"])
    @cog.input("tokenID", type=str, help="tokenID generating prompt", default="0")
    def predict(self, **kwargs):
        yield from super().predict(settings="pixray_pixel", **kwargs)

class Text2Image(BasePixrayPredictor):
    @cog.input("prompts", type=str, help="description of what to draw", default="Robots skydiving high above the city")
    @cog.input("quality", type=str, help="speed vs quality", default="better", options=["draft", "normal", "better", "best"])
    @cog.input("aspect", type=str, help="wide or narrow", default="widescreen", options=["widescreen", "square", "portrait"])
    def predict(self, **kwargs):
        yield from super().predict(settings="text2image", **kwargs)

class Text2Pixel(BasePixrayPredictor):
    @cog.input("prompts", type=str, help="text prompt", default="Manhattan skyline at sunset. #pixelart")
    @cog.input("aspect", type=str, help="wide or narrow", default="widescreen", options=["widescreen", "square", "portrait"])
    @cog.input("pixel_scale", type=float, help="bigger pixels", default=1.0, min=0.5, max=2.0)
    def predict(self, **kwargs):
        yield from super().predict(settings="text2pixel", **kwargs)

class PixrayRaw(BasePixrayPredictor):
    @cog.input("prompts", type=str, help="text prompt", default="Manhattan skyline at sunset. #pixelart")
    @cog.input("settings", type=str, help="yaml settings", default='drawer: pixel\nscale: 2.5\nquality: better')
    def predict(self, prompts, settings):
        ydict = yaml.safe_load(settings)
        yield from super().predict(settings="pixrayraw", prompts=prompts, **ydict)
