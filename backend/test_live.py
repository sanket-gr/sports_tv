import extractor

url = "https://partner.nonamejose.sx/69acc497/7738feef/404ced5a"
print(f"Testing full extraction on: {url}")
result = extractor.extract(url)
print("\nResult:")
for k, v in result.items():
    print(f"  {k}: {v}")
