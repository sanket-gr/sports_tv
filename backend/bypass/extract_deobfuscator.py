import re

with open("player_js.js", "r", encoding="utf-8") as f:
    js = f.read()

# Let's find the shifting block
# It looks like: (function(n,e){const t=le,s=n();for(;;)try{if(parseInt(t(189))...
shift_idx = js.find("function(n,e){const t=le")
if shift_idx != -1:
    # Backtrack to the start of the self-invoking function: (function(n,e){...})(kl,995855);
    # Actually, it's (function(n,e){...})(kl,995855);
    start_shift = js.rfind("(", 0, shift_idx)
    end_shift = js.find("})(kl,995855);", shift_idx) + len("})(kl,995855);")
    shift_code = js[start_shift:end_shift]
    print("Found shifting loop!")
else:
    shift_code = ""
    print("Shifting loop NOT found")

# Let's find function le
le_idx = js.find("function le(")
if le_idx != -1:
    # Find the end of le function
    # It is function le(n,e){const t=kl();return le=function(s,i){return s=s-136,t[s]},le(n,e)}
    end_le = js.find("}", le_idx)
    # The inner function has another }, so let's find the second }
    end_le = js.find("}", end_le + 1)
    le_code = js[le_idx:end_le+1]
    print("Found le function!")
else:
    le_code = ""
    print("le function NOT found")

# Let's find function kl
kl_idx = js.find("function kl()")
if kl_idx != -1:
    # Find the end of kl function. It returns kl=function(){return n},kl()}
    # Let's find the return statement
    ret_idx = js.find("return kl=function(){return n},kl()}", kl_idx)
    end_kl = ret_idx + len("return kl=function(){return n},kl()}")
    kl_code = js[kl_idx:end_kl]
    print("Found kl function!")
else:
    kl_code = ""
    print("kl function NOT found")

# Write them to deobfuscator.js
with open("deobfuscator.js", "w", encoding="utf-8") as out:
    out.write(kl_code + "\n\n")
    out.write(le_code + "\n\n")
    out.write(shift_code + "\n\n")
    
    # Add code to print mappings
    out.write("""
const mappings = {};
for (let i = 136; i < 700; i++) {
    try {
        mappings[i] = le(i);
    } catch(e) {}
}
console.log(JSON.stringify(mappings, null, 2));
""")
print("deobfuscator.js written!")
