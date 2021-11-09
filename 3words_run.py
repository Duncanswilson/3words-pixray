import argparse
import boto3
from git import Repo
from git import Git
import threading
import os
import pixray
import json
from transformers import GPT2LMHeadModel, GPT2TokenizerFast
from sh import git
import numpy as np

device = 'cuda'
model_id = 'gpt2'

def perplexity(prompt):
    model = GPT2LMHeadModel.from_pretrained(model_id).to(device)
    tokenizer = GPT2TokenizerFast.from_pretrained(model_id)
    tokens_tensor = tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")
    loss=model(tokens_tensor.to(device), labels=tokens_tensor.to(device))[0]
    return np.exp(loss.cpu().detach().numpy())


def metadata_helper(tokenID, prompt, num_rerolls, num_inplace):
    #get ssh get out of ssm
    #get the private key for the backend datastore
    #ssm = boto3.client('ssm')
    #parameter = ssm.get_parameter(Name='/github/id_rsa')
    #backend_private_key = parameter['Parameter']['Value']
    score = perplexity(prompt[0] + ' ' + prompt[1] + ' ' + prompt[2])

    #create and upload the metadata

    metadata = {"description": "3words Metadata Standard v1",
                "external_url": "https://3wordsproject.com",
                "image": "https://duncanswilson.github.io/3words-pixray/image/{}.png".format(tokenID),
                "name": prompt,
                "attributes":[
                 {"trait_type":"perplexity","value": str(score)},
                 {"trait_type":"phraseId","value": "blah blah"},
                 {"trait_type":"word1","value": prompt[0]},
                 {"trait_type":"word2","value": prompt[1]},
                 {"trait_type":"word3","value": prompt[2]},
                 {"trait_type":"generation","value": '{}.{}'.format(num_rerolls, num_inplace)}]}

    os.system("cp metadata/{}.json metadata-history/metadata{}-{}-{}.json".format(args.tokenID, args.tokenID, num_rerolls, num_inplace))
    with open('{}.json'.format(tokenID), "wt") as f:
        json.dump(metadata, f)     
    #os.system("git add {}.json".format(tokenID))
    #os.system("git commit -m 'add the metadata for {} generation {}.{}'".format(tokenID, num_rerolls, num_inplace))
    #os.system("git push origin master")

parser = argparse.ArgumentParser(description='blah')
parser.add_argument("--tokenID", type=int, help="")
parser.add_argument("--word1", type=str, help="")
parser.add_argument("--word2", type=str, help="")
parser.add_argument("--word3", type=str, help="")
args = parser.parse_args()

#s3 = boto3.client('s3', region_name='us-east-1')
#s3.download_file('reroll-app', 'queue.json', 'queue.json')

#s3.download_file('reroll-app', 'reroll_log.json', 'reroll_log.json')
#reroll_log = json.load(open("reroll_log.json", "rt"))
os.system("wget https://reroll-app.s3.amazonaws.com/reroll_log.json")

reroll_log = json.loads(open('reroll_log.json').read())
#import pdb; pdb.set_trace()
num_rerolls = len(reroll_log[str(args.tokenID)])
num_inplace = 0
for reroll in reroll_log[str(args.tokenID)]:
    if reroll['_word1'] == args.word1 and reroll['_word2'] == args.word2 and reroll['_word3'] == args.word3:
       if reroll['inPlace']:
           num_inplace +=1 


#move the old image to the backup folder
os.system("cp image/{}.png image-history/{}-{}-{}.png".format(args.tokenID, args.tokenID, num_rerolls, num_inplace))
#os.system("git add image-history/{}-{}-{}.png".format( args.tokenID, num_rerolls, num_inplace))
#os.system("git commit -m 'adding new history of tokenID {}'".format(args.tokenID))
#os.system("push -u origin master")

print("---> Kicking off Metadata Helper Func")
#in a subprocess kick off metadata_helper
prompt =[]
prompt.append(args.word1)
prompt.append(args.word2)
prompt.append(args.word3)



th = threading.Thread(target=metadata_helper, args=(args.tokenID, prompt, num_rerolls, num_inplace))
th.start()

pixray.reset_settings()

pixray.add_settings(quality="better", scale=2.5, aspect='square')
real_prompt = "a clear image of " + prompt[0] + ' ' + prompt[1] + ' ' + prompt[2] + ". #pixelart"
pixray.add_settings(prompts=real_prompt)
pixray.add_settings(drawer='pixel')
pixray.add_settings(output= (str(args.tokenID)+".png"))
settings = pixray.apply_settings()
pixray.do_init(settings)
run_complete = False
while run_complete == False:
    run_complete = pixray.do_run(settings, return_display=True)
    #temp_copy = create_temporary_copy(settings.output)
    #yield pathlib.Path(os.path.realpath(temp_copy))
    #os.system("cp {}.png image/{}.png".format(tokenID, tokenID))
    #os.system("git add image/{}.png".format(tokenID))
    #os.system("git commit -m 'adding iteration {} of tokenID {}'".format(counter, tokenID))
    #os.system("git push origin master")
