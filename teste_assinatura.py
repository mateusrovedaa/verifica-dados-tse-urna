"""Autoteste de assinatura.py com seções reais (pasta amostra/) e adulterações."""
import glob, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assinatura as A

acs = A.carrega_acs()
print("ACs", {k: (v["alg"], v["inicio"], v["fim"]) for k, v in acs.items()})
for vsc in sorted(glob.glob("amostra/*-vota.vsc")):
    sec = vsc.removesuffix("-vota.vsc")
    arqs = {os.path.basename(f): open(f, "rb").read() for f in glob.glob(sec + "-*")}
    t = time.time()
    r = A.verifica_vsc(arqs[os.path.basename(vsc)], arqs, acs)
    print(os.path.basename(sec), r, f"{time.time() - t:.2f}s")
    assert r["ac"] != "INVALIDO" and not (r["hash_falha"] or r["assinatura_falha"] or r["sw_hash_falha"]), r

sec = "amostra/o03221ac0100700090001"
vsc = open(sec + "-vota.vsc", "rb").read()
arqs = {os.path.basename(f): open(f, "rb").read() for f in glob.glob(sec + "-*")}
bu = "o03221ac0100700090001-bu.dat"
adulterado = dict(arqs, **{bu: arqs[bu][:-1] + bytes([arqs[bu][-1] ^ 1])})
assert A.verifica_vsc(vsc, adulterado, acs)["hash_falha"] == [bu]
s = next(s for n, _, s in A.le_entidade(vsc, A.filhos(vsc, A.elemento(vsc, 0))[1])[0] if n == bu)
i = vsc.find(s) + 10
assert A.verifica_vsc(vsc[:i] + bytes([vsc[i] ^ 1]) + vsc[i + 1:], arqs, acs)["assinatura_falha"] == [bu]
print("adulterações detectadas: ok")

# pontos de ordem pequena (0, -1) e (1, 0) não são aceitos como chave Ed521; a chave de uma urna real é
ordem_pequena = [(A.P - 1).to_bytes(66, "little"), (0).to_bytes(66, "little")]
assert not any(A.ed_no_subgrupo(k) for k in ordem_pequena)
cert = A.le_certificado(open("acs/acue2022.der", "rb").read())
assert cert["alg"] == "ed521" and A.ed_no_subgrupo(cert["chave"])
# DER truncado é recusado em vez de lido pela metade
try:
    A.filhos(vsc[:1000], A.elemento(vsc[:1000], 0))
    raise AssertionError("DER truncado aceito")
except ValueError:
    pass
print("ordem pequena e DER truncado recusados: ok")
