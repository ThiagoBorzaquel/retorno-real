#!/usr/bin/env python3
"""Dados públicos de referência -> data/refs.json (séries mensais).
IPCA (SGS 433) e CDI mensal (SGS 4391): Banco Central do Brasil.
CPI EUA (CPIAUCNS): FRED/BLS. USD/BRL fim de mês: Yahoo Finance (gráfico público)."""
import json, csv, io, datetime as dt, urllib.request, urllib.parse as up
UA = {"User-Agent": "Mozilla/5.0 (compatible; RetornoReal/1.0)"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode()
def bcb(s):
    out = {}
    for d in json.loads(get(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{s}/dados/ultimos/260?formato=json")):
        dd, mm, yy = d["data"].split("/"); out[f"{yy}-{mm}"] = float(d["valor"])
    return out
def cpi():
    out = {}
    for r in csv.reader(io.StringIO(get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCNS"))):
        try: out[r[0][:7]] = float(r[1])
        except Exception: pass
    return {k: v for k, v in out.items() if k >= "2005-01"}
def fx():
    r = json.loads(get("https://query1.finance.yahoo.com/v8/finance/chart/BRL%3DX?range=20y&interval=1mo"))["chart"]["result"][0]
    out = {}
    for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]):
        if c: out[dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m")] = round(c, 4)
    return out
R = {"updated": dt.datetime.now(dt.timezone.utc).isoformat()}
for k, f in (("ipca", lambda: bcb(433)), ("cdi", lambda: bcb(4391)), ("cpi", cpi), ("fx", fx)):
    try: R[k] = f()
    except Exception as e: print("erro", k, e); R[k] = {}
json.dump(R, open("data/refs.json", "w"), separators=(",", ":"))
print({k: len(v) for k, v in R.items() if isinstance(v, dict)})
