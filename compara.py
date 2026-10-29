"""Compara os fatos extraídos por processa.py entre si e com o resultado oficial publicado pelo TSE.

Entradas: saida/secoes, saida/votos e saida/rdv (de processa.py); resultado oficial por seção do TSE
(votacao_secao_2026_BR.zip para presidente, votacao_secao_2026_<UF>.zip para governador), baixado para
oficial/ com o SHA-256 registrado em resultados/oficial.sha256. Se hashes_tse/oficial.sha256 existir,
cada arquivo baixado precisa ter o SHA-256 registrado nele, senão o script para.

Saídas em resultados/:
  divergencias.csv       uma linha por problema encontrado (seção, tipo, detalhe)
  fusos_municipios.csv   fuso deduzido para cada município e se difere do padrão da UF
  horarios_secoes.csv    por seção: fuso, abertura/fechamento/último voto em horário de Brasília,
                         votos a partir das 17h e a partir das 19h de Brasília
  resumo.md              números gerais

Regras de horário (todas aqui, para poderem ser revistas):
  - A votação abriu às 8h de Brasília no país todo; a urna registra o horário LOCAL.
    Fuso do município = (hora de abertura mais comum entre as suas seções, arredondada) - 8.
    Isso dispensa uma tabela de municípios e é conferível: fusos_municipios.csv lista os que diferem
    do padrão da UF (esperado: oeste do AM em -2h, Fernando de Noronha em +1h).
  - Encerramento: 17h de Brasília; prorrogado até 19h de Brasília pela decisão do min. Zanin (STF,
    Rcl 101.673, 25/10/2026), depois restrita às seções ainda abertas. Eleitor na fila no horário de
    encerramento ainda vota, então votos pouco depois do limite são esperados.
  - Exterior (ZZ): votação em horário local de cada país; não convertemos para Brasília.
"""
import csv, glob, hashlib, io, os, subprocess, sys, zipfile
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assinatura

OFICIAL = "https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_{}.zip"
PADRAO_UF = {"AC": -2, "AM": -1, "RO": -1, "RR": -1, "MT": -1, "MS": -1}  # Decreto 2.784/1913 (Lei 12.876/2013)
CODIGOS = {"95": "BRANCO", "96": "NULO"}  # NR_VOTAVEL nos arquivos oficiais
# Faixas de horário em Brasília [início, fim): de hora em hora e agrupadas
FAIXAS = ([("antes das 8h", -99, 8)] + [(f"{h}h–{h + 1}h", h, h + 1) for h in range(8, 19)]
          + [("a partir das 19h", 19, 99), ("8h–12h", 8, 12), ("12h–17h", 12, 17), ("a partir das 17h", 17, 99)])
DIA = "20261025"
CARGOS = ("PRESIDENTE", "GOVERNADOR")  # os cargos do resultado oficial por seção
TODAS_UFS = "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ".split()


def ler(padrao):
    for p in sorted(glob.glob(padrao)):
        with open(p, newline="") as f:
            yield from csv.DictReader(f)


def minutos(hhmmss):
    h, m, s = map(int, hhmmss.split(":"))
    return h * 60 + m + s / 60


def para_brasilia(hhmmss, fuso):
    """'15:01:33' local com fuso -2 -> '17:01:33'."""
    if not hhmmss:
        return ""
    h, resto = hhmmss.split(":", 1)
    return f"{int(h) - fuso:02d}:{resto}"


def chave_secao(secao):
    """o03221ac0100700090001 -> ('ac'.upper(), município, zona, seção) como inteiros, igual aos arquivos oficiais."""
    return secao[6:8].upper(), int(secao[8:13]), int(secao[13:17]), int(secao[17:21])

# ---------- resultado oficial ----------


def baixa_oficial(nome):
    path = f"oficial/votacao_secao_2026_{nome}.zip"
    if not os.path.exists(path):
        subprocess.run(["curl", "-sfL", "--retry", "10", "-o", path + ".tmp", OFICIAL.format(nome)], check=True)
        os.replace(path + ".tmp", path)
    return path


def votos_oficiais(path):
    """{(uf, município, zona, seção): {(cargo, número): votos}} do 2º turno."""
    out = defaultdict(Counter)
    with zipfile.ZipFile(path) as z:
        csv_nome = next(n for n in z.namelist() if n.endswith(".csv"))
        with z.open(csv_nome) as f:
            for x in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"):
                if x["NR_TURNO"] != "2":
                    continue
                k = (x["SG_UF"], int(x["CD_MUNICIPIO"]), int(x["NR_ZONA"]), int(x["NR_SECAO"]))
                out[k][(x["DS_CARGO"].upper(), CODIGOS.get(x["NR_VOTAVEL"], x["NR_VOTAVEL"]))] += int(x["QT_VOTOS"])
    return out

# ---------- comparações ----------


def main():
    os.makedirs("oficial", exist_ok=True)
    os.makedirs("resultados", exist_ok=True)
    secoes = list(ler("saida/secoes/*.csv"))
    ufs = sorted({s["uf"] for s in secoes})
    div = []  # (uf, secao, tipo, detalhe)

    # 1. Assinatura digital e arquivos
    for s in secoes:
        if s["ac_certificado"] == "INVALIDO":
            div.append((s["uf"], s["secao"], "certificado da urna não emitido pelas ACs do TSE", s["modelo_urna"]))
        if s["cert_inicio"] and not s["cert_inicio"] <= DIA <= s["cert_fim"]:
            div.append((s["uf"], s["secao"], "certificado da urna fora da validade em 25/10/2026",
                        f"{s['cert_inicio']}-{s['cert_fim']}"))
        for col in ("hash_falha", "assinatura_falha", "sw_hash_falha", "problemas"):
            if s[col]:
                div.append((s["uf"], s["secao"], col, s[col]))

    # 2. Log x BU: cada voto no log deve corresponder a um eleitor no comparecimento do BU
    for s in secoes:
        if s["comparecimento_bu"] and int(s["votos_log"]) != int(s["comparecimento_bu"]):
            div.append((s["uf"], s["secao"], "votos no log diferente do comparecimento no BU",
                        f"log={s['votos_log']} bu={int(s['comparecimento_bu'])}"))

    # 3. BU por dentro: em cada cargo, candidatos + brancos + nulos = total apurado; para presidente,
    #    apurado = comparecimento. Governador pode ter menos: eleitor em trânsito de outra UF vota só para presidente.
    bu = defaultdict(Counter)  # (uf, município, zona, seção) -> {(cargo, número): votos}
    comparecimento = {s["secao"]: s["comparecimento_bu"] for s in secoes}
    apurado, nome_secao_bu = {}, {}
    for v in ler("saida/votos/*.csv"):
        if v["numero"] == "APURADO":
            apurado[(v["secao"], v["cargo"])] = int(v["votos"])
        else:
            bu[chave_secao(v["secao"])][(v["cargo"], v["numero"])] += int(v["votos"])
            nome_secao_bu[chave_secao(v["secao"])] = v["secao"]
    for k, votos in bu.items():
        for cargo in {c for c, _ in votos}:
            secao = nome_secao_bu[k]
            if (secao, cargo) not in apurado:
                div.append((k[0], secao, "BU inconsistente", f"{cargo}: sem total apurado"))
            if k[0] == "ZZ" and cargo != "PRESIDENTE":
                div.append((k[0], secao, "BU inconsistente", f"{cargo}: exterior vota só para presidente"))
    for (secao, cargo), total in apurado.items():
        soma = sum(n for (c, _), n in bu[chave_secao(secao)].items() if c == cargo)
        comp = int(comparecimento[secao] or 0)
        if soma != total or total > comp or (cargo == "PRESIDENTE" and total != comp):
            div.append((secao[6:8].upper(), secao, "BU inconsistente",
                        f"{cargo}: soma={soma} apurado={total} comparecimento={comparecimento[secao]}"))

    # 3b. RDV x BU: os votos recontados um a um no RDV devem dar os totais do BU
    rdv = defaultdict(Counter)
    for v in ler("saida/rdv/*.csv"):
        rdv[chave_secao(v["secao"])][(v["cargo"], v["numero"])] += int(v["votos"])
    for k in rdv:
        for item in sorted(i for i in set(rdv[k]) | set(bu[k]) if i[0] in CARGOS):
            if rdv[k][item] != bu[k][item]:
                div.append((k[0], nome_secao_bu.get(k, ""), "RDV diferente do BU",
                            f"{item[0]} {item[1]}: rdv={rdv[k][item]} bu={bu[k][item]}"))

    # 4. BU x resultado oficial publicado pelo TSE
    esperados = {}
    if os.path.exists("hashes_tse/oficial.sha256"):
        esperados = {l.split()[1]: l.split()[0] for l in open("hashes_tse/oficial.sha256") if l.strip()}
    oficial = defaultdict(Counter)
    with open("resultados/oficial.sha256", "w") as f:
        for nome in ["BR"] + [u for u in ufs if u != "ZZ"]:
            path = baixa_oficial(nome)
            with open(path, "rb") as z:
                h = hashlib.file_digest(z, "sha256").hexdigest()
            if esperados.get(os.path.basename(path), h) != h:
                sys.exit(f"{path} tem SHA-256 {h}, diferente do registrado em hashes_tse/oficial.sha256")
            f.write(f"{h}  {os.path.basename(path)}  {OFICIAL.format(nome)}\n")
            for k, votos in votos_oficiais(path).items():
                if k[0] in ufs:  # o arquivo BR traz todas as UFs; compara só as processadas
                    oficial[k].update(votos)
    # Eleições suplementares e consultas populares do mesmo dia (ex.: prefeito) não estão nesses arquivos:
    # esses cargos ficam fora da comparação e aparecem só nos totais, marcados como não conferidos.
    cargos_oficiais = {c for v in oficial.values() for c, _ in v}
    nome_secao = {chave_secao(s["secao"]): s["secao"] for s in secoes}
    for k in sorted(set(bu) | set(oficial)):
        secao = nome_secao.get(k, "o?????{}{:05d}{:04d}{:04d}".format(k[0].lower(), *k[1:]))
        if k not in bu:
            div.append((k[0], secao, "seção no resultado oficial sem BU publicado", ""))
        elif k not in oficial:
            div.append((k[0], secao, "BU publicado sem seção no resultado oficial", ""))
        else:
            for item in sorted(set(bu[k]) | set(oficial[k])):
                if item[0] in cargos_oficiais and bu[k][item] != oficial[k][item]:
                    div.append((k[0], secao, "BU diferente do resultado oficial",
                                f"{item[0]} {item[1]}: bu={bu[k][item]} oficial={oficial[k][item]}"))

    # 5. Fusos: deduzidos da hora de abertura das urnas de cada município
    aberturas = defaultdict(Counter)
    for s in secoes:
        if s["uf"] != "ZZ" and s["abertura_local"]:
            aberturas[(s["uf"], s["municipio"])][round(minutos(s["abertura_local"]) / 60) - 8] += 1
    fuso = {}
    with open("resultados/fusos_municipios.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["uf", "municipio", "municipio_nome", "fuso_deduzido", "secoes", "secoes_que_concordam", "padrao_uf", "difere_do_padrao"])
        nomes = {(s["uf"], s["municipio"]): s["municipio_nome"] for s in secoes}
        for k, c in sorted(aberturas.items()):
            fuso[k], n = c.most_common(1)[0]
            padrao = PADRAO_UF.get(k[0], 0)
            w.writerow([*k, nomes[k], fuso[k], sum(c.values()), n, padrao, "SIM" if fuso[k] != padrao else ""])

    # 6. Horários em Brasília e votos a partir das 17h e das 19h
    total = Counter()
    por_uf = defaultdict(Counter)
    faixa = defaultdict(Counter)  # faixa -> {coluna: votos}
    with open("resultados/horarios_secoes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["uf", "secao", "fuso", "origem_fuso", "abertura_brasilia", "fechamento_brasilia", "ultimo_voto_brasilia",
                    "votos", "votos_a_partir_17h_brasilia", "votos_a_partir_19h_brasilia"])
        for s in secoes:
            if s["uf"] == "ZZ":
                continue
            k = (s["uf"], s["municipio"])
            fz, origem = (fuso[k], "deduzido") if k in fuso else (PADRAO_UF.get(s["uf"], 0), "padrao_uf")
            hora = [int(s[f"votos_{h:02d}h_local"]) for h in range(24)]
            a17 = sum(hora[17 + fz:])  # hora local 17+fz = 17h de Brasília (fusos são horas inteiras)
            a19 = sum(hora[19 + fz:])
            ultimo = para_brasilia(s["ultimo_voto_local"], fz)
            w.writerow([s["uf"], s["secao"], fz, origem, para_brasilia(s["abertura_local"], fz),
                        para_brasilia(s["fechamento_local"], fz), ultimo, s["votos_log"], a17, a19])
            for c in (total, por_uf[s["uf"]]):
                c["secoes"] += 1
                c["votos"] += int(s["votos_log"])
                c["a17"] += a17
                c["a19"] += a19
                c["secoes_a17"] += a17 > 0
                c["secoes_a19"] += a19 > 0
            brasilia = {h - fz: n for h, n in enumerate(hora)}
            for nome, ini, fim in FAIXAS:
                n = sum(v for h, v in brasilia.items() if ini <= h < fim)
                faixa[nome]["votos"] += n
                faixa[nome]["secoes"] += n > 0

    with open("resultados/divergencias.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["uf", "secao", "tipo", "detalhe"])
        w.writerows(sorted(div))

    # 7. Resumo
    tipos = Counter(t for _, _, t, _ in div)
    totais_bu, totais_oficial = Counter(), Counter()
    for k in bu:
        totais_bu.update(bu[k])
    for k in oficial:
        totais_oficial.update(oficial[k])
    linhas = ["# Auditoria dos arquivos de urna — 2º turno, 25/10/2026", "",
              f"- Seções com arquivos de urna: {len(secoes)} ({', '.join(ufs)})",
              f"- UFs não processadas: {', '.join(sorted(set(TODAS_UFS) - set(ufs))) or 'nenhuma'}",
              f"- Seções no resultado oficial: {len(oficial)}",
              f"- Cargos sem resultado oficial por seção nos arquivos usados (não conferidos): "
              f"{', '.join(sorted({c for c, _ in totais_bu} - cargos_oficiais)) or 'nenhum'}",
              f"- Municípios com fuso diferente do padrão da UF: {sum(1 for k in fuso if fuso[k] != PADRAO_UF.get(k[0], 0))} (ver fusos_municipios.csv)",
              f"- Seções com RDV recontado: {len(rdv)}",
              *[f"- Seções com certificado de urna emitido pela {nome}: {sum(s['ac_certificado'] == nome for s in secoes)}"
                for nome in assinatura.carrega_acs()],
              "", "## Divergências", "", "| tipo | quantidade |", "|---|---|"]
    linhas += [f"| {t} | {n} |" for t, n in tipos.most_common()] or ["| (nenhuma) | 0 |"]
    linhas += ["", "## Votos por horário (Brasília, sem exterior)", "",
               "| UF | seções | votos | a partir das 17h | seções com voto ≥17h | a partir das 19h | seções com voto ≥19h |",
               "|---|---|---|---|---|---|---|"]
    for uf, c in sorted(por_uf.items()) + [("**Total**", total)]:
        linhas.append(f"| {uf} | {c['secoes']} | {c['votos']} | {c['a17']} | {c['secoes_a17']} | {c['a19']} | {c['secoes_a19']} |")
    linhas += ["", "## Votos por faixa de horário (Brasília, sem exterior)", "",
               "| faixa | votos | % dos votos do dia | seções com voto na faixa |", "|---|---|---|---|"]
    with open("resultados/votos_por_faixa.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["faixa_brasilia", "votos", "pct_dos_votos_do_dia", "secoes_com_voto_na_faixa"])
        for nome, _, _ in FAIXAS:
            c = faixa[nome]
            pct = 100 * c["votos"] / total["votos"]
            w.writerow([nome, c["votos"], f"{pct:.4f}", c["secoes"]])
            linhas.append(f"| {nome} | {c['votos']} | {pct:.3f}% | {c['secoes']} |")
    linhas += ["", "## Totais por candidato: BUs publicados x resultado oficial", "",
               "| cargo | número | BUs | oficial | diferença |", "|---|---|---|---|---|"]
    for item in sorted(set(totais_bu) | set(totais_oficial)):
        if item[0] in cargos_oficiais:
            linhas.append(f"| {item[0]} | {item[1]} | {totais_bu[item]} | {totais_oficial[item]} | {totais_bu[item] - totais_oficial[item]} |")
        else:
            linhas.append(f"| {item[0]} | {item[1]} | {totais_bu[item]} | não conferido | |")
    with open("resultados/resumo.md", "w") as f:
        f.write("\n".join(linhas) + "\n")
    print("\n".join(linhas))


if __name__ == "__main__":
    main()
