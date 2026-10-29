"""Verifica o arquivo de assinatura da urna (-vota.vsc, -red.vsc, -sa.vsc) só com a biblioteca padrão.

O que é conferido, seguindo o código de referência do TSE (formato-arquivos-bu-rdv-ass-digital-v2.zip,
python/assinatura_hash.py e python/lib/mr_util.py):
  1. o certificado da urna foi assinado por uma das ACs do TSE (pasta acs/), e o emissor nele
     declarado é essa AC; a validade (início e fim) do certificado é devolvida para conferência;
  2. para cada arquivo listado na assinatura de hardware: SHA-512 do arquivo == hash registrado, e
     a assinatura da urna sobre SHA-512(hash) é válida com a chave do certificado.
A assinatura de software (algoritmo CEPESC) não é pública: dela só conferimos os hashes.

Algoritmos (definidos pelo modelo da urna):
  UE2013/UE2015: ECDSA na curva NIST P-521 (assinatura em DER).
  UE2020/UE2022: Ed521 (padrão ICP-Brasil): EdDSA na curva de Edwards E-521, hash SHAKE-256 de 132 bytes
                 com prefixo "SigEd521\\x00\\x00" (mesma construção do Ed448, RFC 8032).

Layout do arquivo em 2026 (difere da spec v2 publicada: o modelo vem num SEQUENCE no final e
os campos opcionais usam tags de contexto [0] conjuntoChave e [1] certificadoDigital):
  SEQUENCE { assinaturaSW EntidadeAssinatura, assinaturaHW EntidadeAssinatura,
             SEQUENCE { modeloEquipamento ENUMERATED, algoritmo ENUMERATED } }
"""
import base64, hashlib, os

# ---------- leitor DER mínimo ----------
# Cada elemento é (tag, início do elemento, início do conteúdo, fim).


def elemento(b, i):
    """Lê o elemento DER que começa em b[i]."""
    tag, n, ini = b[i], b[i + 1], i + 2
    if n == 0x80:
        raise ValueError("comprimento indefinido não é DER")
    if n & 0x80:  # comprimento longo: os próximos (n & 0x7f) bytes dão o tamanho
        k = n & 0x7F
        n = int.from_bytes(b[ini:ini + k], "big")
        ini += k
    if ini + n > len(b):
        raise ValueError("elemento passa do fim do arquivo")
    return tag, i, ini, ini + n


def filhos(b, e):
    """Elementos contidos em e (um SEQUENCE)."""
    out, i = [], e[2]
    while i < e[3]:
        out.append(elemento(b, i))
        i = out[-1][3]
    return out


def valor(b, e):
    return b[e[2]:e[3]]

# ---------- curvas ----------
# Constantes: Ed521 do padrão ICP-Brasil (as mesmas do ECPy usado pelo TSE); P-521 do NIST FIPS 186-4.

P = 2**521 - 1  # o mesmo primo nas duas curvas

ED_D = P - 376014
ED_N = 0x7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffd15b6c64746fc85f736b8af5e7ec53f04fbd8c4569a8f1f4540ea2435f5180d6b
ED_G = (0x752cb45c48648b189df90cb2296b2878a3bfd9f42fc6c818ec8bf3c9c0c6203913f6ecc5ccc72434b1ae949d568fc99c6059d0fb13364838aa302a940a2f19ba6c, 0xc)

EC_A = P - 3
EC_B = 0x51953eb9618e1c9a1f929a21a0b68540eea2da725b99b315f3b8b489918ef109e156193951ec7e937b1652c0bd3bb1bf073573df883d2c34f1ef451fd46b503f00
EC_N = 0x1fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa51868783bf2f966b7fcc0148f709a5d03bb5c9b8899c47aebb6fb71e91386409
EC_G = (0xc6858e06b70404e9cd9e3ecb662395b4429c648139053fb521f828af606b4d3dbaa14b5e77efe75928fe1dc127a2ffa8de3348b3c1856a429bf97e7e31c2e5bd66,
        0x11839296a789a3bc0045c8a5fb42c7d1bd998f54449579b446817afbd17273e662c97ee72995ef42640c550b9013fad0761353c7086a272c24088be94769fd16650)


def mult(k, ponto, soma, zero):
    """k · ponto pelo método 'dobra e soma'."""
    r = zero
    for bit in bin(k)[2:]:
        r = soma(r, r)
        if bit == "1":
            r = soma(r, ponto)
    return r


def ed_soma(p1, p2):
    """Soma na curva de Edwards x² + y² = 1 + d·x²·y², em coordenadas projetivas (x = X/Z, y = Y/Z)
    para evitar uma divisão por soma. Fórmula única (vale também para dobrar): "add-2007-bl" de
    https://hyperelliptic.org/EFD/g1p/auto-edwards-projective.html com c = 1."""
    (X1, Y1, Z1), (X2, Y2, Z2) = p1, p2
    A = Z1 * Z2 % P
    B = A * A % P
    C = X1 * X2 % P
    D = Y1 * Y2 % P
    E = ED_D * C * D % P
    F, G = B - E, B + E
    return A * F * ((X1 + Y1) * (X2 + Y2) - C - D) % P, A * G * (D - C) % P, F * G % P


def ed_igual(p1, p2):
    (X1, Y1, Z1), (X2, Y2, Z2) = p1, p2
    return (X1 * Z2 - X2 * Z1) % P == 0 and (Y1 * Z2 - Y2 * Z1) % P == 0


def ed_decodifica(e):
    """Ponto Ed521 em 66 bytes little-endian: y, com o bit mais alto guardando a paridade de x.
    Devolve None se a codificação não for canônica ou o ponto não estiver na curva.
    (O denominador d·y² - 1 nunca é zero: d não é quadrado módulo P.)"""
    if len(e) != 66:
        return None
    y = int.from_bytes(e, "little")
    sinal, y = y >> 527, y & ((1 << 527) - 1)
    xx = (y * y - 1) * pow(ED_D * y * y - 1, -1, P) % P
    x = pow(xx, (P + 1) // 4, P)  # raiz quadrada, pois P ≡ 3 (mod 4)
    if y >= P or x * x % P != xx or (x == 0 and sinal):
        return None
    return (P - x if x & 1 != sinal else x), y, 1


def ed_no_subgrupo(chave):
    """A chave pública é um ponto da curva de ordem ED_N (exclui pontos de ordem pequena).
    Com A nesse subgrupo, a equação de ed521_verifica força R também nele."""
    A = ed_decodifica(chave)
    return A is not None and not ed_igual(A, (0, 1, 1)) and ed_igual(mult(ED_N, A, ed_soma, (0, 1, 1)), (0, 1, 1))


def ed521_verifica(chave, msg, assinatura):
    """Ed521: válida se S·G == R + H(R, A, msg)·A."""
    if len(assinatura) != 132:
        return False
    eR, S = assinatura[:66], int.from_bytes(assinatura[66:], "little")
    h = hashlib.shake_256(b"SigEd521\x00\x00" + eR + chave + msg).digest(132)
    h = int.from_bytes(h, "little") % ED_N
    A, R = ed_decodifica(chave), ed_decodifica(eR)
    if S >= ED_N or A is None or R is None:
        return False
    zero = (0, 1, 1)
    return ed_igual(mult(S, (*ED_G, 1), ed_soma, zero), ed_soma(R, mult(h, A, ed_soma, zero)))


def ec_soma(p1, p2):
    """Soma na curva P-521 y² = x³ + a·x + b (None é o ponto no infinito)."""
    if p1 is None: return p2
    if p2 is None: return p1
    (x1, y1), (x2, y2) = p1, p2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if p1 == p2:
        m = (3 * x1 * x1 + EC_A) * pow(2 * y1, -1, P) % P
    else:
        m = (y2 - y1) * pow(x2 - x1, -1, P) % P
    x3 = (m * m - x1 - x2) % P
    return x3, (m * (x1 - x3) - y1) % P


def ecdsa_p521_verifica(chave, digest, assinatura_der):
    """ECDSA P-521. chave = 04||X||Y (ponto não comprimido); assinatura = SEQUENCE { INTEGER r, INTEGER s }."""
    if len(chave) != 133 or chave[0] != 4:
        return False
    Q = (int.from_bytes(chave[1:67], "big"), int.from_bytes(chave[67:], "big"))
    if (Q[1] ** 2 - Q[0] ** 3 - EC_A * Q[0] - EC_B) % P:
        return False  # chave fora da curva
    seq = elemento(assinatura_der, 0)
    campos = filhos(assinatura_der, seq)
    if seq[0] != 0x30 or seq[3] != len(assinatura_der) or [e[0] for e in campos] != [0x02, 0x02]:
        return False
    r, s = (int.from_bytes(valor(assinatura_der, e), "big") for e in campos)
    if not (0 < r < EC_N and 0 < s < EC_N):
        return False
    e, w = int.from_bytes(digest, "big"), pow(s, -1, EC_N)
    ponto = ec_soma(mult(e * w % EC_N, EC_G, ec_soma, None), mult(r * w % EC_N, Q, ec_soma, None))
    return ponto is not None and ponto[0] % EC_N == r


def verifica(alg, chave, m, assinatura):
    """Igual a `verificador.verify(m, assinatura, chave)` do ECPy, usado pelo TSE:
    no Ed521, m é a mensagem; no ECDSA, m já é o digest."""
    if alg == "ed521":
        return ed521_verifica(chave, m, assinatura)
    return ecdsa_p521_verifica(chave, m, assinatura)

# ---------- certificados X.509 ----------

OID_ED521 = bytes.fromhex("2b0601040182dc2c0201")  # 1.3.6.1.4.1.44588.2.1 em DER


def data(der, e):
    """UTCTime (AAMMDD...) ou GeneralizedTime (AAAAMMDD...) -> 'AAAAMMDD'."""
    t = valor(der, e).decode()
    return ("20" + t[:6]) if e[0] == 0x17 else t[:8]


def le_certificado(der):
    """Certificate ::= SEQUENCE { tbs, algoritmo, assinatura }; o TBS tem
    [0] version (opcional), serial, algoritmo, emissor, validade, titular, chave pública.
    Devolve dict com tbs (bytes), alg, chave, sig (do emissor), emissor, titular, inicio e fim ('AAAAMMDD')."""
    tbs, _, sig = filhos(der, elemento(der, 0))
    campos = filhos(der, tbs)
    _, _, emissor, validade, titular, spki = campos[-6:] if campos[0][0] != 0xA0 else campos[1:7]
    alg, chave = filhos(der, spki)
    inicio, fim = (data(der, e) for e in filhos(der, validade))
    # BIT STRING: o 1º byte é o nº de bits não usados (0); o resto é o valor
    return {"tbs": der[tbs[1]:tbs[3]], "alg": "ed521" if OID_ED521 in valor(der, alg) else "ecdsa",
            "chave": valor(der, chave)[1:], "sig": valor(der, sig)[1:],
            "emissor": der[emissor[1]:emissor[3]], "titular": der[titular[1]:titular[3]], "inicio": inicio, "fim": fim}


def carrega_acs(pasta=os.path.join(os.path.dirname(os.path.abspath(__file__)), "acs")):
    """Certificados das ACs do TSE: {nome: le_certificado(...)}."""
    return {nome.removesuffix(".der"): le_certificado(open(os.path.join(pasta, nome), "rb").read())
            for nome in sorted(os.listdir(pasta)) if nome.endswith(".der")}

# ---------- arquivo de assinatura da urna ----------


def le_entidade(b, e):
    """EntidadeAssinatura. Devolve ([(arquivo, hash, assinatura)], hash registrado da lista, bytes da lista, certificado)."""
    data_hora, versao, auto_assinado, conteudo_auto_assinado, *opcionais = filhos(b, e)
    # AutoAssinaturaDigital ::= SEQUENCE { usuario, algoritmoHash, algoritmoAssinatura, assinatura }
    _, _, _, auto_assinatura = filhos(b, auto_assinado)
    # AssinaturaDigital ::= SEQUENCE { tamanho, hash, assinatura }
    _, hash_lista, _ = filhos(b, auto_assinatura)
    cert = next((valor(b, x) for x in opcionais if x[0] == 0x81), None)  # [1] certificadoDigital

    # conteudoAutoAssinado contém: Assinatura ::= SEQUENCE { arquivosAssinados SEQUENCE OF AssinaturaArquivo }
    lista = valor(b, conteudo_auto_assinado)
    (arquivos_assinados,) = filhos(lista, elemento(lista, 0))
    arquivos = []
    for item in filhos(lista, arquivos_assinados):
        nome, ass = filhos(lista, item)  # AssinaturaArquivo ::= SEQUENCE { nomeArquivo, assinatura }
        _, h, s = filhos(lista, ass)     # AssinaturaDigital ::= SEQUENCE { tamanho, hash, assinatura }
        arquivos.append((valor(lista, nome).decode("latin-1"), valor(lista, h), valor(lista, s)))
    return arquivos, valor(b, hash_lista), lista, cert


MODELOS = {13: "UE2013", 15: "UE2015", 20: "UE2020", 22: "UE2022"}


def verifica_vsc(vsc, arquivos_da_secao, acs):
    """Confere a assinatura de uma seção.

    arquivos_da_secao: {nome do arquivo: bytes} com os arquivos publicados.
    Devolve: modelo da urna, ac (qual AC do TSE emitiu e assinou o certificado da urna, ou "INVALIDO"),
    cert_inicio e cert_fim (validade do certificado da urna, 'AAAAMMDD') e listas de nomes:
      ausentes (assinados mas não publicados pelo TSE), hash_falha, assinatura_falha (HW), sw_hash_falha.
    """
    sw, hw, fim = filhos(vsc, elemento(vsc, 0))
    modelo = MODELOS.get(int.from_bytes(valor(vsc, filhos(vsc, fim)[0]), "big"), "?")
    hw_arqs, hw_hash, hw_lista, cert = le_entidade(vsc, hw)
    sw_arqs, sw_hash, sw_lista, _ = le_entidade(vsc, sw)
    if cert.startswith(b"-----BEGIN"):  # UE2020/UE2022 trazem o certificado em PEM
        cert = base64.b64decode(b"".join(l for l in cert.splitlines() if not l.startswith(b"-----")))
    c = le_certificado(cert)
    alg, chave = c["alg"], c["chave"]
    m = c["tbs"] if alg == "ed521" else hashlib.sha512(c["tbs"]).digest()  # mr_util.valida_certificado
    ac = next((nome for nome, a in acs.items()
               if a["alg"] == alg and a["titular"] == c["emissor"] and verifica(alg, a["chave"], m, c["sig"])), "INVALIDO")
    if alg == "ed521" and not ed_no_subgrupo(chave):
        ac = "INVALIDO"

    r = {"modelo": modelo, "ac": ac, "cert_inicio": c["inicio"], "cert_fim": c["fim"],
         "ausentes": [], "hash_falha": [], "assinatura_falha": [], "sw_hash_falha": []}
    if hashlib.sha512(hw_lista).digest() != hw_hash:
        r["hash_falha"].append("(lista HW)")
    if hashlib.sha512(sw_lista).digest() != sw_hash:
        r["sw_hash_falha"].append("(lista SW)")
    for chave_falha, lista in (("hash_falha", hw_arqs), ("sw_hash_falha", sw_arqs)):
        nomes = [nome for nome, _, _ in lista]
        r[chave_falha] += [f"(duplicado) {n}" for n in sorted(set(nomes)) if nomes.count(n) > 1]
        for nome, h, _ in lista:
            if nome not in arquivos_da_secao:
                if nome not in r["ausentes"]:
                    r["ausentes"].append(nome)
            elif hashlib.sha512(arquivos_da_secao[nome]).digest() != h:
                r[chave_falha].append(nome)
    for nome, h, s in hw_arqs:
        if nome in arquivos_da_secao and not verifica(alg, chave, hashlib.sha512(h).digest(), s):
            r["assinatura_falha"].append(nome)  # como em assinatura_hash.valida_assinturas do TSE
    return r
