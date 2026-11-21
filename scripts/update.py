#!/usr/bin/env python3
"""Dados públicos de referência -> data/refs.json (séries mensais).
IPCA (SGS 433) e CDI mensal (SGS 4391): Banco Central do Brasil.
CPI EUA (CPIAUCNS): FRED/BLS. USD/BRL fim de mês: Yahoo Finance (gráfico público)."""
import json, csv, io, datetime as dt, urllib.request, urllib.parse as up
UA = {"User-Agent": "Mozilla/5.0 (compatible; RetornoReal/1.0)"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode()
def bcb(s):
    out = {}
    urls = [
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{s}/dados/ultimos/260?formato=json",
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{s}/dados/ultimos/260",
    ]
    for u in urls:
        try:
            rows = json.loads(get(u))
            for d in rows:
                dd, mm, yy = d["data"].split("/")
                out[f"{yy}-{mm}"] = float(d["valor"])
            if out:
                return out
        except Exception:
            pass
    raise RuntimeError(f"BCB series {s} unavailable")
def cpi():
    out = {}
    try:
        for r in csv.reader(io.StringIO(get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCNS"))):
            try: out[r[0][:7]] = float(r[1])
            except Exception: pass
    except Exception:
        try:
            request = urllib.request.Request(
                "https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0",
                data=json.dumps({"startyear": "2005", "endyear": str(dt.datetime.now().year)}).encode(),
                headers={"Content-type": "application/json", **UA},
                method="POST",
            )
            rows = json.loads(urllib.request.urlopen(request, timeout=30).read().decode())
            for r in rows["Results"]["series"][0]["data"]:
                month = r["period"][1:]
                if month.isdigit():
                    out[f"{r['year']}-{month.zfill(2)}"] = float(r["value"])
        except Exception:
            pass
    return {k: v for k, v in out.items() if k >= "2005-01"}
def fx():
    out = {}
    try:
        r = json.loads(get("https://query1.finance.yahoo.com/v8/finance/chart/BRL%3DX?range=20y&interval=1mo"))["chart"]["result"][0]
        for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]):
            if c: out[dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m")] = round(c, 4)
    except Exception:
        try:
            for r in csv.reader(io.StringIO(get("https://stooq.com/q/d/l/?s=usdbrl&i=m"))):
                if len(r) == 2 and r[0][:4].isdigit():
                    try: out[r[0][:7]] = round(float(r[1]), 4)
                    except Exception: pass
        except Exception:
            pass
    return out
R = {"updated": dt.datetime.now(dt.timezone.utc).isoformat()}
old = {}
try:
    old = json.load(open("data/refs.json", "r", encoding="utf-8"))
except Exception:
    pass
for k, f in (("ipca", lambda: bcb(433)), ("cdi", lambda: bcb(4391)), ("cpi", cpi), ("fx", fx)):
    try:
        fresh = f()
        R[k] = fresh or old.get(k, {})
    except Exception as e:
        print("erro", k, e)
        R[k] = old.get(k, {})
with open("data/refs.json", "w", encoding="utf-8") as h:
    json.dump(R, h, ensure_ascii=False, separators=(",", ":"))
print({k: len(v) for k, v in R.items() if isinstance(v, dict)})
