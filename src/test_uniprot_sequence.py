import requests


UNIPROT_ID = "P00533"

url = f"https://rest.uniprot.org/uniprotkb/{UNIPROT_ID}.fasta"

response = requests.get(url, timeout=30)

print("HTTP 상태 코드:", response.status_code)
print()

print(response.text[:1000])