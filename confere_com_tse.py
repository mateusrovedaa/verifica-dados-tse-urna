"""Conferência cruzada com implementações independentes:
  1. assinatura: cada seção da pasta é validada com o código de referência do TSE e com assinatura.py;
  2. RDV: cada rdv.dat é decodificado pela spec ASN.1 do TSE (asn1tools) e por processa.le_rdv;
  3. vetores: assinaturas Ed521 geradas pelo ECPy (a biblioteca que o TSE usa) e ECDSA P-521 geradas pela
     biblioteca cryptography (OpenSSL) têm de ser aceitas por assinatura.py, e as adulteradas recusadas.
As implementações têm de concordar em tudo.

Código do TSE: tse-ref/pkg/python (formato-arquivos-bu-rdv-ass-digital-v2.zip, SHA-256 1e423054...a84a235).
Dependências (só deste script): asn1tools, pyOpenSSL e ECPy instalado do git (o TSE orienta assim; ver README).
Única adaptação: spec/assinatura-2026.asn1 (layout de 2026; diferenças em spec/assinatura-2026.diff).

Uso: python confere_com_tse.py [pasta]
"""
import glob, hashlib, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "tse-ref", "pkg", "python"))
sys.path.insert(0, AQUI)
import asn1tools, random
from collections import Counter
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from ecpy.curves import Curve
from ecpy.eddsa import EDDSA
from ecpy.keys import ECPrivateKey
from lib.mr_util import converte_certificado_para_x509, decode_x509, extrai_chave_do_certificado, valida_certificado, _modelo
import assinatura, processa

SPEC = asn1tools.compile_files([os.path.join(AQUI, "spec", "assinatura-2026.asn1")], codec="ber", numeric_enums=True)
SPEC_RDV = asn1tools.compile_files([os.path.join(AQUI, "tse-ref", "pkg", "spec", "rdv.asn1")], codec="ber", numeric_enums=True)


def rdv_tse(b):
    """Contagem do RDV pela spec do TSE, no mesmo formato de processa.le_rdv."""
    c = Counter()
    for eleicao in SPEC_RDV.decode("EntidadeResultadoRDV", b)["rdv"]["eleicoes"][1]:
        for vc in eleicao["votosCargos"]:
            tipo_cargo, n = vc["idCargo"]
            cargo = processa.CARGOS_RDV.get(n, str(n)) if tipo_cargo == "cargoConstitucional" else f"CONSULTA {n}"
            for voto in vc["votos"]:
                t = voto["tipoVoto"]
                c[(cargo, voto["digitacao"] if t in (1, 2) else "BRANCO" if t in (3, 5) else "NULO")] += 1
    return sorted((cargo, num, q) for (cargo, num), q in c.items())


def vetores(n=20):
    """Assinaturas geradas por outras bibliotecas: válidas aceitas, adulteradas recusadas."""
    rnd = random.Random(2026)
    ed, curva = EDDSA(hashlib.shake_256, hash_len=132), Curve.get_curve("Ed521")
    for i in range(n):
        msg = rnd.randbytes(64)
        priv = ECPrivateKey(rnd.randrange(1, curva.order), curva)
        chave = bytes(curva.encode_point(ed.get_public_key(priv, hashlib.shake_256, hash_len=132).W))
        sig = ed.sign(msg, priv)
        assert assinatura.ed521_verifica(chave, msg, sig) and assinatura.ed_no_subgrupo(chave), i
        assert not assinatura.ed521_verifica(chave, msg + b"x", sig), i
        assert not assinatura.ed521_verifica(chave, msg, sig[:-1] + bytes([sig[-1] ^ 1])), i

        k = ec.generate_private_key(ec.SECP521R1())
        digest = hashlib.sha512(msg).digest()
        der = k.sign(digest, ec.ECDSA(utils.Prehashed(hashes.SHA512())))
        pub = k.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
        assert assinatura.ecdsa_p521_verifica(pub, digest, der), i
        assert not assinatura.ecdsa_p521_verifica(pub, hashlib.sha512(msg + b"x").digest(), der), i
    print(f"vetores: {n} Ed521 (ECPy) e {n} ECDSA P-521 (OpenSSL) aceitos; adulterações recusadas")


def valida_tse(vsc, arquivos):
    """Mesmos passos de assinatura_hash.py do TSE (verifica_hashes + valida_assinturas),
    devolvidos no mesmo formato de assinatura.verifica_vsc para comparação."""
    ent = SPEC.decode("EntidadeAssinaturaEcourna", vsc)
    modelo = _modelo(ent["equipamento"]["modeloEquipamento"])
    r = {"modelo": str(modelo).replace(" ", ""), "cert_ok": None, "ausentes": set(),
         "hash_falha": set(), "assinatura_falha": set(), "sw_hash_falha": set()}
    for campo, falhas in (("assinaturaSW", "sw_hash_falha"), ("assinaturaHW", "hash_falha")):
        entidade = ent[campo]
        if hashlib.sha512(entidade["conteudoAutoAssinado"]).digest() != entidade["autoAssinado"]["assinatura"]["hash"]:
            r[falhas].add(f"(lista {campo[-2:]})")
        for arq in SPEC.decode("Assinatura", entidade["conteudoAutoAssinado"])["arquivosAssinados"]:
            nome, h = arq["nomeArquivo"], arq["assinatura"]["hash"]
            if nome not in arquivos:
                r["ausentes"].add(nome)
            elif hashlib.sha512(arquivos[nome]).digest() != h:
                r[falhas].add(nome)
    hw = ent["assinaturaHW"]
    x509, _, chave, verificador = extrai_chave_do_certificado(
        decode_x509(converte_certificado_para_x509(hw["certificadoDigital"], modelo)))
    r["cert_ok"] = valida_certificado(x509, verificador)
    for arq in SPEC.decode("Assinatura", hw["conteudoAutoAssinado"])["arquivosAssinados"]:
        nome, h, s = arq["nomeArquivo"], arq["assinatura"]["hash"], arq["assinatura"]["assinatura"]
        if nome in arquivos and not verificador.verify(hashlib.sha512(h).digest(), s, chave):
            r["assinatura_falha"].add(nome)
    return r


def main(pasta):
    acs = assinatura.carrega_acs()
    divergencias = 0
    vscs = sorted(glob.glob(os.path.join(pasta, "*.vsc")))
    for vsc_path in vscs:
        secao = vsc_path.rsplit("-", 1)[0]
        arquivos = {os.path.basename(f): open(f, "rb").read() for f in glob.glob(secao + "-*")}
        vsc = arquivos[os.path.basename(vsc_path)]
        tse = valida_tse(vsc, arquivos)
        r = assinatura.verifica_vsc(vsc, arquivos, acs)
        nosso = {"modelo": r["modelo"], "cert_ok": r["ac"] != "INVALIDO",
                 **{k: set(r[k]) for k in ("ausentes", "hash_falha", "assinatura_falha", "sw_hash_falha")}}
        if nosso != tse:
            divergencias += 1
            print("DIVERGÊNCIA", os.path.basename(secao), tse, nosso)
        for nome, b in arquivos.items():
            if nome.endswith("-rdv.dat") and processa.le_rdv(b) != rdv_tse(b):
                divergencias += 1
                print("DIVERGÊNCIA RDV", nome)
    print(f"{len(vscs)} seções conferidas com o código do TSE (assinatura e RDV), {divergencias} divergências")
    return divergencias


if __name__ == "__main__":
    vetores()
    sys.exit(1 if main(sys.argv[1] if len(sys.argv) > 1 else "amostra") else 0)
