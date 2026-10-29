"""Baixa os arquivos de uma seção direto do zip da UF no TSE, sem baixar o zip inteiro.

Lê só o índice do zip e os trechos da seção, por requisições HTTP Range. Serve para conferir à mão
qualquer seção, por exemplo os casos de resultados/casos_investigados.md.

Uso: python baixa_secao.py o03221es5793200090085 [pasta]     (padrão: secoes/<seção>/)
"""
import io, os, sys, urllib.request, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from processa import URL


class ArquivoRemoto(io.RawIOBase):
    """Arquivo remoto somente leitura: cada read() vira uma requisição HTTP Range."""

    def __init__(self, url):
        self.url, self.pos = url, 0
        self.tamanho = int(urllib.request.urlopen(urllib.request.Request(url, method="HEAD")).headers["Content-Length"])

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, deslocamento, origem=0):
        self.pos = [deslocamento, self.pos + deslocamento, self.tamanho + deslocamento][origem]
        return self.pos

    def read(self, n=-1):
        fim = self.tamanho if n < 0 else min(self.tamanho, self.pos + n)
        if self.pos >= fim:
            return b""
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{fim - 1}"})
        dados = urllib.request.urlopen(req, timeout=120).read()
        self.pos += len(dados)
        return dados


if __name__ == "__main__":
    secao = sys.argv[1]
    pasta = sys.argv[2] if len(sys.argv) > 2 else os.path.join("secoes", secao)
    z = zipfile.ZipFile(ArquivoRemoto(URL.format(secao[6:8].upper())))
    nomes = [n for n in z.namelist() if n.startswith(secao + "-")]
    if not nomes:
        sys.exit(f"seção {secao} não encontrada")
    os.makedirs(pasta, exist_ok=True)
    for n in nomes:
        with open(os.path.join(pasta, n), "wb") as f:
            f.write(z.read(n))  # zipfile confere o CRC de cada arquivo
        print(os.path.join(pasta, n))
