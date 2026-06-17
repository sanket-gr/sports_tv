import re

with open("player_js.js", "r", encoding="utf-8") as f:
    js = f.read()

# Let's find 'function kl'
idx = js.find("function kl()")
if idx == -1:
    idx = js.find("kl=function")
    print("Found kl=function at", idx)
else:
    print("Found function kl() at", idx)

if idx != -1:
    # Print the code from idx to the end of the file or next 50,000 characters
    print(js[idx:idx+20000])
