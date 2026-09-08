# -*- coding: utf-8 -*-
"""
Extrai os dados de "CAMPOS ESTAGIO - 2026.2 (1).xlsx" e gera:
  public/locations.json  (um registro por campo/atividade, com lat/long)
  public/filters.json    (valores unicos para os filtros da pagina)

Coordenadas:
  1) reaproveitadas do locations.json atual quando o nome do campo casa
  2) geocodificadas via OpenStreetMap/Nominatim (com cache local)
  3) overrides manuais em MANUAL_COORDS

Uso:  python public/2026_data/extract_2026.py
"""
import hashlib, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.abspath(os.path.join(BASE, ".."))
XLSX = os.path.join(BASE, "CAMPOS ESTAGIO - 2026.2 (1).xlsx")
# Fonte de coordenadas ja conhecidas (dados 2025). NAO usar o proprio output,
# senao coordenadas ruins de uma execucao anterior sao "confirmadas".
OLD_LOCATIONS = os.path.join(BASE, "locations_2025_ref.json")
CACHE_FILE = os.path.join(BASE, "geocode_cache.json")
OUT_LOCATIONS = os.path.join(PUBLIC, "locations.json")
OUT_FILTERS = os.path.join(PUBLIC, "filters.json")
UNRESOLVED_FILE = os.path.join(BASE, "coordenadas_nao_encontradas.json")

WEEKDAYS = {1: "DOMINGO", 2: "SEGUNDA", 3: "TERÇA", 4: "QUARTA",
            5: "QUINTA", 6: "SEXTA", 7: "SÁBADO"}
ORDINAIS = {1: "PRIMEIRO", 2: "SEGUNDO", 3: "TERCEIRO", 4: "QUARTO", 5: "QUINTO",
            6: "SEXTO", 7: "SÉTIMO", 8: "OITAVO", 9: "NONO", 10: "DÉCIMO",
            11: "DÉCIMO PRIMEIRO", 12: "DÉCIMO SEGUNDO"}

# Coordenadas conferidas manualmente. A chave e um trecho distintivo do nome
# (comparado por "contains" contra a chave normalizada do campo).
MANUAL_COORDS = {
    "AMBULATORIO IGREJA DO CARMO": [-19.93990, -43.93190],
    "BALEIA": [-19.92233, -43.89828],
    "LUXEMBURGO": [-19.95006, -43.95874],
    "MARIO PENNA": [-19.95006, -43.95874],
    "CERSAM BARREIRO": [-19.99823, -44.00649],
    "VIDA NOVA": [-19.76186, -43.98804],
    "OTILIA LEVINDA": [-19.76186, -43.98804],
    "CUIDAR PALMITAL": [-19.61840, -43.89330],
    "CUIDAR VILA MARIA": [-19.62230, -43.88900],
    "CUIDAR LAPINHA": [-19.59588, -43.90841],
    "CUIDAR AERONAUTAS": [-19.63360, -43.87990],
    "CUIDAR CAMPINHO": [-19.65170, -43.88600],
    "LINDOURO AVELAR": [-19.62770, -43.89020],
    "SANTA CASA LAGOA SANTA": [-19.62770, -43.89020],
    "HEAL": [-19.83300, -44.00500],
    "HOSPITAL ESPIRITA ANDRE LUIZ": [-19.83300, -44.00500],
    "LIFE CENTER": [-19.93850, -43.92850],
    "VERA CRUZ": [-19.93850, -43.92850],
    "OCTAVIANO NEVES": [-19.91800, -43.93600],
    "PIRATININGA": [-19.80960, -43.98680],
    "ANIBAL MACHADO": [-19.88460, -43.79840],
    "MG 20 MONTE AZUL": [-19.79200, -43.95400],
    "JARDIM DOS COMERCIARIOS": [-19.80300, -43.99400],
    "CELVIA": [-19.69200, -43.92300],
    "SABARA UPA III": [-19.88900, -43.80200],
    "PADRE LAZARO PEREIRA CRISPIM": [-19.88900, -43.80200],
    "UPA 24 HORAS PREFEITO LUIZ ISSA": [-19.69150, -43.92330],
    "AMB DE REF DOENCAS INFEC E PARASITARIA": [-19.88700, -43.80500],
    "SAO BENEDITO": [-19.77050, -43.85400],
    "CS ITAIPU": [-19.98500, -44.03200],
    "VILA IMPERIAL": [-19.86800, -43.94300],
    "CS CARLOS RENATO DIAS": [-19.83900, -43.91900],
    "AMILCAR VIANNA MARTINS": [-19.85400, -43.94900],
    "ADELMOLANDIA": [-19.88900, -43.80800],
}

# Centroides das cidades (fallback aproximado)
CITY_COORDS = {
    "BELO HORIZONTE": [-19.9167, -43.9345],
    "LAGOA SANTA": [-19.6272, -43.8903],
    "SABARÁ": [-19.8846, -43.8062],
    "VESPASIANO": [-19.6919, -43.9233],
    "SANTA LUZIA": [-19.7699, -43.8515],
    "PEDRO LEOPOLDO": [-19.6180, -44.0430],
    "CONFINS": [-19.6353, -43.9686],
    "IBIRITÉ": [-20.0217, -44.0589],
    "CONTAGEM": [-19.9320, -44.0537],
    "BETIM": [-19.9678, -44.1980],
    "NOVA LIMA": [-19.9858, -43.8467],
    "DIVINÓPOLIS": [-20.1447, -44.8912],
    "GOVERNADOR VALADARES": [-18.8512, -41.9494],
    "CONCEIÇÃO DO MATO DENTRO": [-19.0369, -43.4247],
    "DIAMANTINA": [-18.2494, -43.6003],
    "NOVA SERRANA": [-19.8760, -44.9847],
    "MARIO CAMPOS": [-20.0855, -44.1230],
    "PATROCÍNIO": [-18.9439, -46.9925],
    "ITAÚNA": [-20.0757, -44.5766],
    "CAMPO BELO": [-20.8942, -45.2777],
    "CARMO DO CAJURU": [-20.1856, -44.7681],
    "TEIXEIRAS": [-20.6472, -42.8583],
    "CONSELHEIRO PENA": [-19.1728, -41.4747],
    "LUZ": [-19.7986, -45.6858],
}


def strip_accents(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def clean_name(raw):
    """Limpa o nome do campo de preceptoria para exibicao."""
    if raw is None:
        return ""
    s = str(raw).replace("\n", " ").strip()
    s = re.split(r"\s*->", s)[0]                    # remove anotacoes "-> enviado ..."
    s = re.sub(r"\s*-?\s*CNES\s*:?\s*\d+", "", s, flags=re.I)
    s = re.sub(r"\s*-\s*(PBH|FHEMIG)\b", "", s, flags=re.I)
    s = re.sub(r"\s+S\.?\s*A\.?\s*$", "", s)
    s = re.sub(r"\s*-\s*MG$", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" -")
    return s


def clean_city(raw):
    if raw is None:
        return ""
    s = str(raw).replace("\n", " ")
    s = re.split(r"\(", s)[0]
    s = re.sub(r"\s*-\s*MG\b", "", s, flags=re.I)
    s = re.sub(r"\s{2,}", " ", s).strip()
    fixes = {"SABARA": "SABARÁ", "IBIRITE": "IBIRITÉ", "PATROCINIO": "PATROCÍNIO",
             "ITAUNA": "ITAÚNA", "DIVINOPOLIS": "DIVINÓPOLIS"}
    return fixes.get(strip_accents(s).upper().strip(), s.strip().upper())


def norm_key(s):
    """Chave de comparacao entre nomes de locais."""
    s = strip_accents(str(s or "")).upper()
    s = re.split(r"CNES", s)[0]
    s = re.sub(r"HTTPS?://\S+", "", s)
    s = s.replace("\n", " ")
    s = re.sub(r"\bPBH\b|\bFHEMIG\b|\bS\.?A\.?\b|POLICLINIA|POLICLINICA|- MG", " ", s)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    for p in ("CENTRO DE SAUDE ", "CS ", "UBS ", "PSF ", "USF ", "ESF ",
              "UNIDADE BASICA DE SAUDE ", "UNIDADE DE SAUDE DA FAMILIA ",
              "CENTRO DE ESPECIALIDADES MEDICAS ", "CEM "):
        if s.startswith(p):
            s = s[len(p):]
    return s.strip()


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1, sort_keys=True)


def geocode(query, cache):
    if query in cache:
        return cache[query]
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": query, "format": "json", "limit": 1, "countrycodes": "br"})
    req = urllib.request.Request(url, headers={"User-Agent": "faminas-estagios-map/1.0 (contato: coordenacao)"} )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
    except Exception as e:
        print(f"  ! erro geocode '{query}': {e}")
        data = []
    time.sleep(1.1)
    result = None
    if data:
        result = [round(float(data[0]["lat"]), 6), round(float(data[0]["lon"]), 6),
                  data[0].get("display_name", "")]
    cache[query] = result
    save_cache(cache)
    return result


def main():
    try:
        import openpyxl
    except ImportError:
        sys.exit("Instale openpyxl:  pip install openpyxl")

    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    header = [str(h).strip() if h else h for h in rows[0]]

    records = []
    for r in rows[1:]:
        if all(c is None for c in r):
            continue
        records.append(dict(zip(header, r)))
    print(f"Linhas de dados: {len(records)}")

    # indice do locations.json atual
    old_index = {}
    if os.path.exists(OLD_LOCATIONS):
        with open(OLD_LOCATIONS, encoding="utf-8") as f:
            for o in json.load(f):
                k = norm_key(o.get("local", ""))
                if k and k not in old_index:
                    old_index[k] = (o["latitude"], o["longitude"],
                                    o.get("endereco", ""))
    print(f"Locais no arquivo atual: {len(old_index)}")

    cache = load_cache()

    def resolve_coords(campo_limpo, cidade, endereco_real):
        k = norm_key(campo_limpo)
        if k in ("A DEFINIR", ""):
            if cidade in CITY_COORDS:
                lat, lon = CITY_COORDS[cidade]
                return lat, lon, "cidade", f"{cidade} - MG (a definir)"
        for mk, (lat, lon) in MANUAL_COORDS.items():
            if mk in k:
                return lat, lon, "manual", endereco_real
        if k in old_index:
            lat, lon, end = old_index[k]
            return lat, lon, "reused", (endereco_real or end)
        # correspondencia por subtrecho (nomes longos e distintivos)
        cands = [(ok, v) for ok, v in old_index.items()
                 if len(ok) >= 12 and (f" {ok} " in f" {k} " or f" {k} " in f" {ok} ")]
        if cands:
            ok, (lat, lon, end) = max(cands, key=lambda c: len(c[0]))
            return lat, lon, "reused", (endereco_real or end)
        # geocodificacao
        expandido = campo_limpo
        expandido = re.sub(r"^CS ", "Centro de Saude ", expandido, flags=re.I)
        expandido = re.sub(r"^(UBS|USF|ESF|PSF) ", "", expandido, flags=re.I)
        expandido = re.sub(r"^(SABARA|VESPASIANO) ", "", expandido, flags=re.I)
        queries = []
        if endereco_real:
            queries.append(endereco_real)
        queries.append(f"{expandido}, {cidade}, Minas Gerais, Brasil")
        queries.append(f"{campo_limpo}, {cidade}, Minas Gerais, Brasil")
        for q in queries:
            g = geocode(q, cache)
            if g and "brasil" in g[2].lower():
                return g[0], g[1], "geocoded", (endereco_real or g[2])
        if cidade in CITY_COORDS:
            lat, lon = CITY_COORDS[cidade]
            # jitter deterministico (~ ate 700m) para nao empilhar campos distintos
            h = int(hashlib.md5(k.encode()).hexdigest(), 16)
            lat = round(lat + ((h % 1000) - 500) / 80000, 6)
            lon = round(lon + ((h // 1000 % 1000) - 500) / 80000, 6)
            return lat, lon, "cidade", (endereco_real or f"{cidade} - MG (localização aproximada)")
        return None, None, "none", endereco_real

    coord_by_key = {}     # cache dentro da execucao
    locations = []
    unresolved = []
    next_id = 1

    for rec in records:
        campo = clean_name(rec.get("CAMPO DE PRECEPTORIA"))
        if not campo or campo.upper() == "A DEFINIR":
            campo = campo or "A DEFINIR"
        cidade = clean_city(rec.get("LOCALIZACAO"))

        end_raw = rec.get("ENDEREÇO")
        endereco_real, endereco_url = "", None
        if end_raw:
            end_raw = str(end_raw).strip()
            if end_raw.lower().startswith("http"):
                endereco_url = end_raw
            else:
                endereco_real = end_raw

        key = (norm_key(campo), cidade)
        if key not in coord_by_key:
            coord_by_key[key] = resolve_coords(campo, cidade, endereco_real)
        lat, lon, src, endereco_final = coord_by_key[key]

        if lat is None:
            if campo not in [u["campo"] for u in unresolved]:
                unresolved.append({"campo": campo, "cidade": cidade})

        periodo = rec.get("PERIODO")
        try:
            periodo = int(periodo)
        except (TypeError, ValueError):
            periodo = None

        dia_raw = rec.get("DIA DA SEMANA")
        dia = ""
        if isinstance(dia_raw, str) and dia_raw.strip().upper() == "ESCALA":
            dia = "ESCALA"
        elif hasattr(dia_raw, "day"):
            dia = WEEKDAYS.get(dia_raw.day, "")
        else:
            try:
                dia = WEEKDAYS.get(int(dia_raw), "")
            except (TypeError, ValueError):
                dia = ""

        try:
            estudante = int(rec.get("QTDE. DE ALUNOS"))
        except (TypeError, ValueError):
            estudante = 0

        try:
            ch = int(rec.get("C.H. SEMANAL"))
        except (TypeError, ValueError):
            ch = None

        atividade = (str(rec.get("ATIVIDADE DE CAMPO") or "").strip().upper()
                     .replace("NUCLEO", "NÚCLEO"))
        especialidade = (str(rec.get("ESPECIALIDADE")).strip()
                         if rec.get("ESPECIALIDADE") else None)
        preceptor = (str(rec.get("PRECEPTOR")).strip()
                     if rec.get("PRECEPTOR") else "A definir")
        coordenador = (str(rec.get("NOME COORDENADOR DO NÚCLEO/INTERNATO")).strip()
                       if rec.get("NOME COORDENADOR DO NÚCLEO/INTERNATO") else "")
        turma = str(rec.get("TURMA")).strip() if rec.get("TURMA") is not None else ""
        turno = str(rec.get("TURNO")).strip().upper() if rec.get("TURNO") else ""

        if lat is None:
            continue  # sem coordenada -> fora do mapa (fica listado em unresolved)

        locations.append({
            "id": next_id,
            "local": campo,
            "cidade": cidade,
            "endereco": endereco_final or (cidade + " - MG"),
            "endereco_url": endereco_url,
            "disciplina": str(rec.get("DISCIPLINA") or "").strip(),
            "atividade": atividade,
            "especialidade": especialidade,
            "coordenador": coordenador,
            "preceptor": preceptor,
            "estudante": estudante,
            "periodo": periodo,
            "periodo_original": (ORDINAIS.get(periodo, str(periodo))
                                 if periodo else ""),
            "turma": turma,
            "categoria": especialidade or atividade,
            "dia": dia,
            "turno": turno,
            "ch_semanal": ch,
            "latitude": lat,
            "longitude": lon,
            "geocode_source": src,
        })
        next_id += 1

    # filtros
    def uniq(field):
        vals = {l[field] for l in locations if l.get(field)}
        return sorted(vals)

    filters = {
        "disciplinas": uniq("disciplina"),
        "atividades": uniq("atividade"),
        "especialidades": uniq("especialidade"),
        "periodos": [ORDINAIS.get(p, str(p)) for p in sorted(
            {l["periodo"] for l in locations if l["periodo"]})],
        "preceptores": sorted({l["preceptor"] for l in locations
                               if l["preceptor"] and l["preceptor"] != "A definir"}),
        "cidades": uniq("cidade"),
    }

    with open(OUT_LOCATIONS, "w", encoding="utf-8") as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)
    with open(OUT_FILTERS, "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)
    with open(UNRESOLVED_FILE, "w", encoding="utf-8") as f:
        json.dump(unresolved, f, ensure_ascii=False, indent=2)

    src_counts = {}
    for l in locations:
        src_counts[l["geocode_source"]] = src_counts.get(l["geocode_source"], 0) + 1
    print(f"\nRegistros gerados: {len(locations)}")
    print(f"Origem das coordenadas: {src_counts}")
    print(f"Campos sem coordenada: {len(unresolved)} -> {UNRESOLVED_FILE}")
    for u in unresolved:
        print(f"   - {u['campo']} ({u['cidade']})")


if __name__ == "__main__":
    main()
