"""Extrai fatos dos arquivos de urna do 2º turno de 2026 (TSE), seção por seção, e apaga o zip da UF.

Este script só extrai (tudo em horário LOCAL da urna). Fusos, regras de horário e comparações
ficam em compara.py, para poderem ser revistos sem baixar tudo de novo.

Saídas:
  saida/secoes/<UF>.csv   uma linha por seção: BU (aptos, comparecimento, abertura, fechamento),
                          log (votos por hora local) e verificação da assinatura digital
  saida/votos/<UF>.csv    votos por cargo/candidato lidos do BU impresso (imgbu)
  saida/rdv/<UF>.csv      os mesmos totais recontados voto a voto no RDV (registro digital do voto)
  saida/zips/<UF>.sha256  SHA-256 do zip baixado do TSE. Se hashes_tse/<UF>.sha256 existir, o zip
                          baixado precisa ter o mesmo SHA-256, senão o script para.
  saida/extras/<UF>.txt   arquivos do zip fora do padrão de nome do TSE (se houver)
  amostra_tse/<UF>/       arquivos de 1% das seções (escolha fixa pelo SHA-256 do nome), para
                          confere_com_tse.py validar com o código do próprio TSE

Pressupostos, conferidos nos arquivos reais de 2026:
  - nomes dos arquivos: <secao>-<sufixo>, secao = fpppppuuMMMMMZZZZSSSS (README do TSE)
  - log.jez é um zip com logd.dat (texto latin-1, "dd/mm/aaaa hh:mm:ss" no início da linha);
    log de urna substituída vem como outro .jez/.zip dentro dele
  - cada voto gera no log uma linha "O voto do eleitor foi computado" (salvo reinício logo após o voto)
  - rdv.dat segue spec/rdv.asn1 do pacote do TSE (BER, tags implícitas)

Duas regras na contagem do log, porque alguns pacotes do TSE trazem logs a mais (casos em
resultados/casos_investigados.md); o que for ignorado fica registrado em colunas próprias:
  - um log aninhado que só declara outra seção ("Seção Eleitoral: NNNN") é ignorado;
  - linhas de voto idênticas (mesmo horário, urna e código de verificação) contam uma vez só.
  - imgbu.dat é o BU impresso: texto com blocos "----CARGO----" de candidatos e totais

Uma UF com os dois CSVs gerados é pulada (permite retomar). Apague saida/ para refazer tudo.
"""
import csv, hashlib, io, os, re, subprocess, sys, zipfile
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assinatura

URL = "https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/arqurnatot/bu_imgbu_logjez_rdv_vscmr_2026_2t_{}.zip"
DIA = "25/10/2026"
UFS = "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ".split()
SECAO = re.compile(r"^[os]\d{5}[a-z]{2}\d{13}$")
COLS = (["uf", "secao", "municipio", "municipio_nome", "zona", "aptos", "comparecimento_bu",
         "abertura_local", "fechamento_local", "votos_log", "primeiro_voto_local", "ultimo_voto_local"]
        + [f"votos_{h:02d}h_local" for h in range(24)]
        + ["logs_outra_secao_ignorados", "linhas_voto_repetidas_ignoradas",
           "modelo_urna", "ac_certificado", "cert_inicio", "cert_fim", "assinados_nao_publicados",
           "hash_falha", "assinatura_falha", "sw_hash_falha", "problemas"])

# ---------- log ----------


def linhas_votos(log_text):
    """Linhas de voto computado no dia do 2º turno."""
    return [linha for linha in log_text.splitlines()
            if linha.startswith(DIA) and "O voto do eleitor foi computado" in linha]


def horarios_votos(textos, secao):
    """Horário local (hh:mm:ss) de cada voto da seção (número com 4 dígitos), somando todos os logs do pacote.
    Devolve (horários, logs de outra seção ignorados, linhas repetidas ignoradas)."""
    linhas, outra = [], 0
    for t in textos:
        declaradas = set(re.findall(r"Seção Eleitoral: (\d{4})", t)) - {"0000"}  # 0000: urna de contingência antes de assumir a seção
        if declaradas and secao not in declaradas:
            outra += 1
            continue
        linhas += linhas_votos(t)
    unicas = set(linhas)
    return sorted(linha[11:19] for linha in unicas), outra, len(linhas) - len(unicas)


def textos_log(jez):
    """Todos os logd* do pacote, inclusive pacotes aninhados (urna substituída)."""
    z = zipfile.ZipFile(io.BytesIO(jez))
    for n in z.namelist():
        if n.startswith("logd"):
            yield z.read(n).decode("latin-1")
        elif n.endswith((".jez", ".zip")):
            yield from textos_log(z.read(n))

# ---------- RDV ----------

CARGOS_RDV = {1: "PRESIDENTE", 3: "GOVERNADOR", 11: "PREFEITO"}  # CargoConstitucional em spec/rdv.asn1


def le_rdv(b):
    """Reconta o RDV: [(cargo, numero, votos)], numero = número digitado, BRANCO ou NULO.
    EntidadeResultadoRDV ::= SEQUENCE { cabecalho, urna, rdv SEQUENCE { pleito, fase, identificacao,
    historico, eleicoes [1]/[2] SEQUENCE OF Eleicao } }; o último campo de cada Eleicao é votosCargos
    (SEQUENCE OF { idCargo, quantidadeEscolhas, votos SEQUENCE OF Voto { tipoVoto, digitacao OPTIONAL } })."""
    f, v = assinatura.filhos, assinatura.valor
    inteiro = lambda e: int.from_bytes(v(b, e), "big")
    _, _, rdv = f(b, assinatura.elemento(b, 0))
    eleicoes = f(b, rdv)[-1]
    contagem = {}
    for eleicao in f(b, eleicoes):
        for votos_cargo in f(b, f(b, eleicao)[-1]):
            id_cargo, _, votos = f(b, votos_cargo)
            # [1] cargo constitucional ou [2] consulta livre (tags 0x81 / 0x82)
            cargo = CARGOS_RDV.get(inteiro(id_cargo), str(inteiro(id_cargo))) if id_cargo[0] == 0x81 else f"CONSULTA {inteiro(id_cargo)}"
            for voto in f(b, votos):
                campos = f(b, voto)
                tipo = inteiro(campos[0])  # TipoVoto: 1 legenda, 2 nominal, 3/5 branco, 4/6/7/8/9 nulo
                numero = v(b, campos[1]).decode() if tipo in (1, 2) else "BRANCO" if tipo in (3, 5) else "NULO"
                contagem[(cargo, numero)] = contagem.get((cargo, numero), 0) + 1
    return [(c, n, q) for (c, n), q in sorted(contagem.items())]

# ---------- BU impresso ----------


def primeiro(regex, texto):
    """Primeiro grupo da primeira linha que casa com a regex, ou "" se não houver."""
    m = re.search(regex, texto, re.M)
    return m.group(1) if m else ""


def le_bu(img):
    """Do BU impresso: cabeçalho e lista (cargo, numero, nome, votos). numero BRANCO/NULO/APURADO para totais."""
    t = img.decode("latin-1").split("===== BU DIGITAL", 1)[0]  # o resto é binário (BU digital e certificado)
    cab = {"municipio_nome": primeiro(r"^Município\s+\d+\n\s*(\S.*?)\s*$", t),
           "aptos": primeiro(r"^Eleitores aptos\s+(\d+)", t),
           "comparecimento_bu": primeiro(r"^Comparecimento\s+(\d+)", t),
           "abertura_local": primeiro(r"^Horário de abertura\s+(\S+)", t),
           "fechamento_local": primeiro(r"^Horário de fechamento\s+(\S+)", t)}
    # Cada cargo: linha "----CARGO----", candidatos ("  NOME   NUM  VOTOS"), totais, e termina em "Código Verificador".
    votos = []
    for cargo, bloco in re.findall(r"^-{3,}([A-ZÀ-Ú ]+?)-{3,}\n(.*?)(?=^Código Verificador)", t, re.M | re.S):
        for nome, num, v in re.findall(r"^  (\S.*?)\s+(\d+)\s+(\d+)$", bloco, re.M):
            votos.append((cargo, num, nome, int(v)))
        for rot, chave in (("Brancos", "BRANCO"), ("Nulos", "NULO"), ("Total Apurado", "APURADO")):
            if m := re.search(rf"^{rot}\s+(\d+)", bloco, re.M):
                votos.append((cargo, chave, "", int(m.group(1))))
    return cab, votos

# ---------- uma seção ----------

_zip, _acs = None, None


def _abre(zpath):
    """Cada processo do pool abre o zip uma vez."""
    global _zip, _acs
    _zip, _acs = zipfile.ZipFile(zpath), assinatura.carrega_acs()


def de_sufixo(arquivos, *sufixos):
    """Conteúdos dos arquivos da seção com um dos sufixos (ex.: imgbu.dat, imgbusa.dat)."""
    return [d for n, d in sorted(arquivos.items()) if n.endswith(sufixos)]


def processa_secao(args):
    uf, secao, nomes = args
    arquivos = {n: _zip.read(n) for n in nomes}
    vscs = de_sufixo(arquivos, ".vsc")
    logs = de_sufixo(arquivos, "-log.jez", "-logsa.jez")
    rdvs = de_sufixo(arquivos, "-rdv.dat")
    imgs = de_sufixo(arquivos, "-imgbu.dat", "-imgbusa.dat")
    problemas = [f"sem {tipo}" for tipo, lista in (("assinatura", vscs), ("log", logs), ("BU impresso", imgs)) if not lista]
    problemas += [f"{len(lista)} arquivos de {tipo}" for tipo, lista in (("assinatura", vscs), ("BU impresso", imgs)) if len(lista) > 1]

    try:
        hs, outra, repetidas = horarios_votos([txt for log in logs for txt in textos_log(log)], secao[17:21])
    except (zipfile.BadZipFile, KeyError, ValueError) as e:
        hs, outra, repetidas, problemas = [], 0, 0, problemas + [f"log ilegível: {e}"]
    rdv = []
    for d in rdvs:
        try:
            rdv += le_rdv(d)
        except (IndexError, ValueError) as e:
            problemas.append(f"RDV ilegível: {e}")
    if imgs and not rdvs and not any(n.endswith("-imgbusa.dat") for n in arquivos):
        problemas.append("sem RDV")
    por_hora = [0] * 24
    for h in hs:
        por_hora[int(h[:2])] += 1
    cab, votos = le_bu(imgs[0]) if imgs else ({}, [])
    if imgs and not cab["comparecimento_bu"]:
        problemas.append("BU impresso sem comparecimento")

    ass = [""] * 8
    if vscs:
        try:
            a = assinatura.verifica_vsc(vscs[0], arquivos, _acs)
            ass = ([a["modelo"], a["ac"], a["cert_inicio"], a["cert_fim"], len(a["ausentes"])]
                   + [";".join(a[k]) for k in ("hash_falha", "assinatura_falha", "sw_hash_falha")])
        except (IndexError, ValueError, TypeError, AttributeError) as e:  # arquivo de assinatura fora do formato
            problemas.append(f"assinatura ilegível: {type(e).__name__}")
    linha = ([uf, secao, secao[8:13], cab.get("municipio_nome", ""), secao[13:17]]
             + [cab.get(c, "") for c in ("aptos", "comparecimento_bu", "abertura_local", "fechamento_local")]
             + [len(hs), hs[0] if hs else "", hs[-1] if hs else ""] + por_hora + [outra, repetidas]
             + ass + [";".join(problemas)])
    amostra = int(hashlib.sha256(secao.encode()).hexdigest(), 16) % 100 == 0
    return linha, [[uf, secao, *v] for v in votos], [[uf, secao, *v] for v in rdv], (arquivos if amostra else None)

# ---------- uma UF ----------


def baixa(uf):
    return subprocess.Popen(["curl", "-sfL", "--retry", "10", "-C", "-", "-o", f"dados/{uf}.zip", URL.format(uf)])


def sha256_arquivo(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while bloco := f.read(1 << 20):
            h.update(bloco)
    return h.hexdigest()


def processa_uf(uf, processos):
    zpath, spath, vpath, rpath = (f"dados/{uf}.zip", f"saida/secoes/{uf}.csv", f"saida/votos/{uf}.csv", f"saida/rdv/{uf}.csv")
    h = sha256_arquivo(zpath)
    if os.path.exists(f"hashes_tse/{uf}.sha256") and open(f"hashes_tse/{uf}.sha256").read().split()[0] != h:
        sys.exit(f"{uf}.zip tem SHA-256 {h}, diferente do registrado em hashes_tse/{uf}.sha256: o TSE mudou o arquivo")
    with open(f"saida/zips/{uf}.sha256", "w") as f:
        f.write(f"{h}  {uf}.zip  {URL.format(uf)}\n")
    with zipfile.ZipFile(zpath) as z:
        nomes = z.namelist()
    secoes, extras = {}, []
    for n in nomes:
        prefixo = n.split("-", 1)[0]
        if "-" in n and SECAO.match(prefixo):
            secoes.setdefault(prefixo, []).append(n)
        else:
            extras.append(n)
    if extras:
        with open(f"saida/extras/{uf}.txt", "w") as f:
            f.write("\n".join(extras) + "\n")
    os.makedirs(f"amostra_tse/{uf}", exist_ok=True)
    with open(spath + ".tmp", "w", newline="") as fs, open(vpath + ".tmp", "w", newline="") as fv, \
            open(rpath + ".tmp", "w", newline="") as fr, Pool(processos, initializer=_abre, initargs=(zpath,)) as pool:
        ws, wv, wr = csv.writer(fs), csv.writer(fv), csv.writer(fr)
        ws.writerow(COLS)
        wv.writerow(["uf", "secao", "cargo", "numero", "nome", "votos"])
        wr.writerow(["uf", "secao", "cargo", "numero", "votos"])
        tarefas = [(uf, s, secoes[s]) for s in sorted(secoes)]
        for linha, votos, rdv, amostra in pool.imap(processa_secao, tarefas, chunksize=20):
            ws.writerow(linha)
            wv.writerows(votos)
            wr.writerows(rdv)
            for n, d in (amostra or {}).items():
                with open(f"amostra_tse/{uf}/{n}", "wb") as f:
                    f.write(d)
    os.replace(spath + ".tmp", spath)
    os.replace(vpath + ".tmp", vpath)
    os.replace(rpath + ".tmp", rpath)
    os.remove(zpath)


def feito(uf):
    return all(os.path.exists(f"saida/{d}/{uf}.csv") for d in ("secoes", "votos", "rdv"))


def demo():
    log = ("25/10/2026 07:00:00\tINFO\t1\tGAP\tSeção Eleitoral: 0009\tA\n"
           "27/09/2026 16:59:00\tINFO\t1\tVOTA\tO voto do eleitor foi computado\tB\n"
           "25/10/2026 16:59:59\tINFO\t1\tVOTA\tO voto do eleitor foi computado\tC\n"
           "25/10/2026 17:00:00\tINFO\t1\tVOTA\tO voto do eleitor foi computado\tD\n"
           "25/10/2026 15:10:00\tINFO\t1\tVOTA\tEleitor foi habilitado\tE\n")
    outra_secao = "25/10/2026 09:00:00\tINFO\t2\tVOTA\tO voto do eleitor foi computado\tF\nSeção Eleitoral: 0112\n"
    contingencia = "Seção Eleitoral: 0000\n25/10/2026 10:00:00\tINFO\t3\tVOTA\tO voto do eleitor foi computado\tG\n"
    assert horarios_votos([log, log, outra_secao, contingencia], "0009") == (["10:00:00", "16:59:59", "17:00:00"], 1, 2)
    rdv = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "amostra/o03221ac0100700090001-rdv.dat"), "rb").read()
    assert ("PRESIDENTE", "13", 68) in le_rdv(rdv) and ("PRESIDENTE", "22", 149) in le_rdv(rdv), le_rdv(rdv)
    bu = ("Município                        01007\n                BUJARI\n\n"
          "Eleitores aptos                   0308\nComparecimento                    0232\n"
          "Horário de abertura           06:00:01\nHorário de fechamento         15:01:33\n"
          "--------------PRESIDENTE--------------\nNome do candidato       Num cand Votos\n\n"
          "  LULA                        13  0068\n  FLAVIO BOLSONARO            22  0149\n\n"
          "--------------------------------------\nEleitores aptos                   0308\n"
          "Total de votos Nominais           0217\nBrancos                           0002\n"
          "Nulos                             0013\nTotal Apurado                     0232\n\n"
          "Código Verificador: 0.003.143.276\n============= BU DIGITAL =============\n").encode("latin-1")
    cab, v = le_bu(bu)
    assert cab == {"municipio_nome": "BUJARI", "aptos": "0308", "comparecimento_bu": "0232",
                   "abertura_local": "06:00:01", "fechamento_local": "15:01:33"}, cab
    assert v == [("PRESIDENTE", "13", "LULA", 68), ("PRESIDENTE", "22", "FLAVIO BOLSONARO", 149),
                 ("PRESIDENTE", "BRANCO", "", 2), ("PRESIDENTE", "NULO", "", 13), ("PRESIDENTE", "APURADO", "", 232)]
    assert SECAO.match("o03221ac0100700090001") and not SECAO.match("buHlUR4nayk79dLskY=.id")
    print("ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["demo"]:
        demo(); sys.exit()
    for d in ("dados", "saida/secoes", "saida/votos", "saida/rdv", "saida/zips", "saida/extras", "amostra_tse"):
        os.makedirs(d, exist_ok=True)
    ufs = [u for u in (sys.argv[1:] or UFS) if not feito(u)]
    processos = max(1, (os.cpu_count() or 2) - 2)
    # baixa a próxima UF enquanto processa a atual (no máximo 2 zips em disco)
    download = baixa(ufs[0]) if ufs else None
    for i, uf in enumerate(ufs):
        if download.wait() != 0:
            sys.exit(f"falha ao baixar {uf}")
        download = baixa(ufs[i + 1]) if i + 1 < len(ufs) else None
        processa_uf(uf, processos)
        print("feito", uf, flush=True)
