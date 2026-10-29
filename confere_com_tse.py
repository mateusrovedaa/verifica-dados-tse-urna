"""Conferência cruzada: valida as seções da pasta amostra/ com o código de referência do TSE e compara
com o resultado de assinatura.py. As duas implementações têm de concordar em todas as seções.

Código do TSE: tse-ref/pkg/python (formato-arquivos-bu-rdv-ass-digital-v2.zip, SHA-256 1e423054...a84a235).
Dependências (só deste script): asn1tools, pyOpenSSL e ECPy instalado do git (o TSE orienta assim; ver README).
Única adaptação: spec/assinatura-2026.asn1 (layout de 2026; diferenças em spec/assinatura-2026.diff).

Uso: python confere_com_tse.py [pasta]
"""
import glob, hashlib, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "tse-ref", "pkg", "python"))
sys.path.insert(0, AQUI)
import asn1tools
from lib.mr_util import converte_certificado_para_x509, decode_x509, extrai_chave_do_certificado, valida_certificado, _modelo
import assinatura

SPEC = asn1tools.compile_files([os.path.join(AQUI, "spec", "assinatura-2026.asn1")], codec="ber", numeric_enums=True)


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
    print(f"{len(vscs)} seções conferidas com o código do TSE, {divergencias} divergências")
    return divergencias


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1] if len(sys.argv) > 1 else "amostra") else 0)
