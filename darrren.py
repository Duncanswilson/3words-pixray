import pixray

prompts = ["death is a disease", "ass to ass", "faith in chaos", "people are amazing", "i was perfect", "i love alice"]
for prompt in prompts: 
  real_prompt = "A clear image of " + prompt + ". #pixelart"
  pixray.reset_settings()
  pixray.add_settings(quality="better", scale=2.5, aspect='square')
  pixray.add_settings(prompts=real_prompt)
  pixray.add_settings(drawer='pixel')
  pixray.add_settings(output= (prompt+".png"))
  settings = pixray.apply_settings()
  pixray.do_init(settings)
  run_complete = False
  while run_complete == False:
      run_complete = pixray.do_run(settings, return_display=True)
