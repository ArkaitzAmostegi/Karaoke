import requests



CABECERA = {"User-Agent": "Karaoke casero de Arkaitz"}


def buscar(consulta):
    r = requests.get("https://lrclib.net/api/search",
                    params={"q": consulta},
                    headers=CABECERA,
                    timeout=10)
    r.raise_for_status()
    return r.json()


def descargar(lrclib_id):
    r = requests.get(f"https://lrclib.net/api/get/{lrclib_id}", headers=CABECERA, timeout=10)
    r.raise_for_status()
    return r.json()