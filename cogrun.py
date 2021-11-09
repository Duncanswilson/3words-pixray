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
from transformers import BertLMHeadModel, BertTokenizerFast
import threading

device = 'cuda'
model_id = 'bert-large-cased'
model = BertLMHeadModel.from_pretrained(model_id).to(device)
tokenizer = BertTokenizerFast.from_pretrained(model_id)

class JSONifiedState():
        """Store the state of scanned blocks and all events.

        All state is an in-memory dict.
        Simple load/store massive JSON on start up.
        """

        def __init__(self):
            self.state = None
            self.fname = "test-state.json"
            # How many second ago we saved the JSON file
            self.last_save = 0
            self.new_rerolls = 0

        def reset(self):
            """Create initial state of nothing scanned."""
            self.state = {
                "last_scanned_block": 0,
                "blocks": {},
            }

        def restore(self, filename):
            """Restore the last scan state from a file."""
            try:
                self.state = json.load(open(filename, "rt"))
                print(f"Restored the state, previously {self.state['last_scanned_block']} blocks have been scanned")
            except (IOError, json.decoder.JSONDecodeError):
                print("State starting from scratch")
                self.reset()

        def save(self):
            """Save everything we have scanned so far in a file."""
            with open(self.fname, "wt") as f:
                # import pdb; pdb.set_trace()
                json.dump(self.state, f)
            self.last_save = time.time()

        def get_last_scanned_block(self):
            """The number of the last block we have stored."""
            return self.state["last_scanned_block"]

        def delete_data(self, since_block):
            """Remove potentially reorganised blocks from the scan data."""
            for block_num in range(since_block, self.get_last_scanned_block()):
                if block_num in self.state["blocks"]:
                    del self.state["blocks"][block_num]

        def start_chunk(self, block_number, chunk_size):
            pass

        def end_chunk(self, block_number):
            """Save at the end of each block, so we can resume in the case of a crash or CTRL+C"""
            # Next time the scanner is started we will resume from this block
            self.state["last_scanned_block"] = block_number

            # Save the database file for every minute
            if time.time() - self.last_save > 60:
                self.save()

        def process_event(self, block_when, event, queue) -> str:
            """Record a ReRoll event in our "database"."""
            # Events are keyed by their transaction hash and log index
            # One transaction may contain multiple events
            # and each one of those gets their own log index
            self.new_rerolls += 1
            # event_name = event.event # "Transfer"
            log_index = event.logIndex  # Log index within the block
            # transaction_index = event.transactionIndex  # Transaction index within the block
            txhash = event.transactionHash.hex()  # Transaction hash
            block_number = event.blockNumber

            # Convert ERC-20 Transfer event to our internal format
            # import pdb; pdb.set_trace()
            args = event.args
            reroll = {
                "_word1": args["word1"],
                "_word2": args["word2"],
                "_word3": args["word3"],
                "tokenID": args["tokenId"],
                "inPlace": args["inPlace"],
                "timestamp": block_when.isoformat(),
            }

            # Create empty dict as the block that contains all transactions by txhash
            if block_number not in self.state["blocks"]:
                self.state["blocks"][block_number] = {}

            block = self.state["blocks"][block_number]
            if txhash not in block:
                # We have not yet recorded any transfers in this transaction
                # (One transaction may contain multiple events if executed by a smart contract).
                # Create a tx entry that contains all events by a log index
                self.state["blocks"][block_number][txhash] = {}

            # Record ERC-20 transfer in our database
            self.state["blocks"][block_number][txhash][log_index] = reroll

            queue.enqueue(reroll)
            # Return a pointer that allows us to look up this event later if needed
            return f"{block_number}-{txhash}-{log_index}"

def perplexity(prompt):
    tokens_tensor = tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")
    loss=model(tokens_tensor, labels=tokens_tensor)[0]
    return np.exp(loss.cpu().detach().numpy())

# https://stackoverflow.com/a/6587648/1010653
import tempfile, shutil
def create_temporary_copy(src_path):
    _, tf_suffix = os.path.splitext(src_path)
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"tempfile{tf_suffix}")
    shutil.copy2(src_path, temp_path)
    return temp_path

def metadata_helper(tokenID, prompt):
    #get ssh get out of ssm
    #get the private key for the backend datastore
    ssm = boto3.client('ssm')
    parameter = ssm.get_parameter(Name='/github/id_rsa')
    backend_private_key = parameter['Parameter']['Value']
    #pull down the "backend" from github
    with open('id_rsa', 'w') as outfile:
        outfile.write(private_key)
    os.chmod('id_rsa', 0o600)
    git_ssh_identity_file = os.path.expanduser('id_rsa')
    git_ssh_cmd = 'ssh -i %s' % git_ssh_identity_file
    if not exists(pixelNFTbackend):
        with Git().custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
             Repo.clone_from('git@github.com:Duncanswilson/pixelNFTbackend.git', 'pixelNFTbackend/', branch='main')

    #reroll log loading
    reroll_log = json.loads(open('reroll_log.json'))
    num_rerolls = len(reroll_log[tokenID])
    num_inplace = 0
    for reroll in reroll_log[tokenID]:
        if reroll['_word1'] == word1 and reroll['_word2'] == word2 and reroll['_word3'] == word3:
            num_inplace +=1 
    #compute the perplexity
    score = perplexity(prompt)

    #create and upload the metadata

    metadata = {"description": "3words Metadata Standard v1",
                "external_url": "http://duncanscottwilson.com/3words-pixray/",
                "image": "http://duncanscottwilson.com/3words-pixray/image/{}.png".format(tokenID),
                "name": prompt,
                "attributes":[
                 {"trait_type":"perplexity","value": score},
                 {"trait_type":"phraseId","value": phraseId},
                 {"trait_type":"word1","value": word1},
                 {"trait_type":"word2","value": word2},
                 {"trait_type":"word3","value": word3},
                 {"trait_type":"generation","value": '{}.{}'.format(num_rerolls, num_inplace)}]}

    os.system("cd metadata/")
    with open('{}.json'.format(tokenID), "wt") as f:
        json.dump(metadata, f)     
    os.system("git add {}.json".format(tokenID))
    os.system("git commit -m 'add the metadata for {} generation {}.{}'".format(tokenID, num_rerolls, num_inplace))
    os.system("git push origin master")

class BasePixrayPredictor(cog.Predictor):
    def setup(self):
        print("---> BasePixrayPredictor Setup")
        os.environ['TORCH_HOME'] = 'models/'


        # SWAP THIS OUT FOR: the private key for the public datastore eventually
        # ssm = boto3.client('ssm')
        # parameter = ssm.get_parameter(Name='/github/g4_key')
        # backend_private_key = parameter['Parameter']['Value']
        #
        # with open('g4_key', 'w') as outfile:
        #     outfile.write(private_key)
        # os.chmod('g4_key', 0o600)
        # git_ssh_identity_file = os.path.expanduser('g4_key')
        # git_ssh_cmd = 'ssh -i %s' % git_ssh_identity_file
        # if not exists(pixelNFTbackend):
        #     with Git().custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
        #          Repo.clone_from('git@github.com:Duncanswilson/3words-pixray.git', '3words-pixray/', branch='main')

    # Define the input types for a prediction
    @cog.input("settings", type=str, help="Default settings to use")
    @cog.input("tokenID", type=str, help="TokenID")
    @cog.input("prompts", type=str, help="Text Prompts")
    def predict(self, settings, tokenID, prompts, **kwargs):
        """Run a single prediction on the model"""
        
        print("---> Kicking off Metadata Helper Func")

        #in a subprocess kick off metadata_helper
        th = threading.Thread(target=metadata_helper, args=(tokenID, prompts))
        th.start()
        
        
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
        #pixray.add_settings(**base_settings)
        #pixray.add_settings(**kwargs)
        pixray.add_settings(quality="better", scale=2.5, aspect='square')
        real_prompt = "a clear image of " + prompts + ". #pixelart"
        pixray.add_settings(prompts=real_prompt)
        #pixray.add_settings(skip_args=True)
	#add name to output here
        pixray.add_settings(output= (tokenID+".png"))
        settings = pixray.apply_settings()
        pixray.do_init(settings)
        run_complete = False
        counter = 0
        while run_complete == False:
            run_complete = pixray.do_run(settings, return_display=True)
            temp_copy = create_temporary_copy(settings.output)
            yield pathlib.Path(os.path.realpath(temp_copy))
            os.system("cp {}.png images/{}.png".format(tokenID, tokenID))
            os.system("git add images/{}.png".format(tokenID))
            os.system("git commit -m 'adding iteration {} of tokenID {}'".format(counter, tokenID))
            os.system("git push origin master")
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
