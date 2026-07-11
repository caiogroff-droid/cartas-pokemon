import requests

session = requests.Session()

session.get(
    "https://www.ligapokemon.com.br/",
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

r = session.get(
    "https://www.ligapokemon.com.br/?view=cards/card&card=Spiritomb%20C%20(003/016)&ed=PTHD&num=003",
    headers={
        "Referer": "https://www.ligapokemon.com.br/"
    }
)

print(r.status_code)
print(r.text[:500])