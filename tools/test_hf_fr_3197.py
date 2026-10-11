from transformers import MarianMTModel, MarianTokenizer
name='Helsinki-NLP/opus-mt-en-fr'
tok=MarianTokenizer.from_pretrained(name)
model=MarianMTModel.from_pretrained(name)
texts=['DASHBOARD // LIVE STATUS','Apply current options or enable safe FPS mode in one click.','OPEN RECOVERY']
batch=tok(texts,return_tensors='pt',padding=True,truncation=True)
out=model.generate(**batch,max_new_tokens=100)
print([tok.decode(x,skip_special_tokens=True) for x in out])
