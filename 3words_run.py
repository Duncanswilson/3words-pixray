import argparse
import boto3
from git import Repo
from git import Git
from transformers import BertLMHeadModel, BertTokenizerFast
import threading
import os
import pixray
import json

def metadata_helper(tokenID, prompt, num_rerolls, num_inplace):
    #get ssh get out of ssm
    #get the private key for the backend datastore
    model = BertLMHeadModel.from_pretrained(model_id).to(device)
    tokenizer = BertTokenizerFast.from_pretrained(model_id)
    ssm = boto3.client('ssm')
    parameter = ssm.get_parameter(Name='/github/id_rsa')
    backend_private_key = parameter['Parameter']['Value']
    score = perplexity(prompt)

    #create and upload the metadata

    metadata = {"description": "3words Metadata Standard v1",
                "external_url": "https://3wordsproject.com",
                "image": "https://duncanswilson.github.io/3words-pixray/image/{}.png".format(tokenID),
                "name": prompt,
                "attributes":[
                 {"trait_type":"perplexity","value": score},
                 {"trait_type":"phraseId","value": "blah blah"},
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

parser = argparse.ArgumentParser(description='blah')
parser.add_argument("--tokenID", type=int, help="")
parser.add_argument("--prompt", type=str, help="")
args = parser.parse_args()


s3 = boto3.client('s3', region_name='us-east-1')
s3.download_file('reroll-app', 'reroll_log.json', 'reroll_log.json')
reroll_log = json.load(open("reroll_log.json", "rt"))



num_rerolls = len(reroll_log[args.tokenID])
num_inplace = 0
for reroll in reroll_log[args.tokenID]:
    if reroll['_word1'] == word1 and reroll['_word2'] == word2 and reroll['_word3'] == word3:
        num_inplace +=1 


#move the old image to the backup folder
os.system("cp images/{}.png images-history/{}-{}-{}.png".format(args.tokenID, num_rerolls, num_inplace))


print("---> Kicking off Metadata Helper Func")
#in a subprocess kick off metadata_helper
th = threading.Thread(target=metadata_helper, args=(args.tokenID, args.prompt, num_rerolls, num_inplace))
th.start()



pixray.reset_settings()

pixray.add_settings(quality="better", scale=2.5, aspect='square')
real_prompt = "a clear image of " + prompts + ". #pixelart"
pixray.add_settings(prompts=real_prompt)
pixray.add_settings(output= (tokenID+".png"))
settings = pixray.apply_settings()
pixray.do_init(settings)
run_complete = False
counter = 0
while run_complete == False:
    run_complete = pixray.do_run(settings, return_display=True)
    #temp_copy = create_temporary_copy(settings.output)
    #yield pathlib.Path(os.path.realpath(temp_copy))
    os.system("cp {}.png images/{}.png".format(tokenID, tokenID))
    os.system("git add images/{}.png".format(tokenID))
    os.system("git commit -m 'adding iteration {} of tokenID {}'".format(counter, tokenID))
    os.system("git push origin master")
    count += 1
