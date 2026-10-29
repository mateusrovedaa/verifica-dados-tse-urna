# Auditoria dos arquivos de urna — Eleições 2026, 2º turno

Auditoria independente e reprodutível dos arquivos que o TSE publica para cada seção eleitoral do 2º turno
de 25/10/2026: boletim de urna (BU), registro digital do voto (RDV), log da urna e arquivo de assinatura digital.

As perguntas respondidas:

1. **Os arquivos são autênticos?** O certificado de cada urna foi emitido pelas autoridades certificadoras
   do TSE, e cada arquivo tem hash e assinatura digital válidos.
2. **Log e BU contam a mesma coisa?** Cada voto registrado no log corresponde a um eleitor no comparecimento do BU.
3. **O BU fecha por dentro?** Em cada cargo, candidatos + brancos + nulos = total apurado.
4. **Os BUs somam o resultado oficial?** Os votos de cada seção conferem com o resultado oficial por seção publicado pelo TSE.
5. **Quantos votos foram dados depois das 17h e das 19h (horário de Brasília)?** O horário foi prorrogado até 19h
   pela decisão do min. Cristiano Zanin (STF, Rcl 101.673), depois restrita às seções ainda abertas.

Resultados: [`resultados/resumo.md`](resultados/resumo.md). Cada divergência encontrada foi investigada em
[`resultados/casos_investigados.md`](resultados/casos_investigados.md).

## Resultado em uma página

**Os arquivos conferem.** Nas 499.207 seções (Brasil e exterior):

- **Hashes e assinaturas digitais:** todos válidos, sem nenhuma falha. Uma amostra de 1% (5.011 seções) foi validada também com o código do próprio TSE, e o resultado foi o mesmo.
- **Resultado oficial:** a soma dos boletins de urna é igual ao resultado oficial, voto a voto, seção por seção.
- **Log x BU:** os votos registrados no log de cada urna batem com o boletim. A exceção são 10 seções, cada uma explicada em [casos_investigados.md](resultados/casos_investigados.md), e nenhuma delas muda os números abaixo.

### Votos por horário (Brasília, só Brasil)

| horário | votos | % dos votos do dia | seções com voto no horário |
|---|---:|---:|---:|
| 8h às 12h | 76.972.075 | 60,20% | 497.895 |
| 12h às 17h | 50.848.439 | 39,77% | 497.770 |
| 17h às 18h | 32.337 | 0,025% | 28.783 |
| 18h às 19h | 1.982 | 0,002% | 1.662 |
| **17h em diante¹** | **34.330** | **0,027%** | **29.854** |
| **Total** | **127.854.844** | **100%** | **497.897** |

¹ Inclui 11 votos depois das 19h, um em cada uma de 11 seções: BA (2), RJ (4) e SP (5).

- Os horários vêm do log de cada urna, que registra cada voto com hora e minuto. O log grava a hora local, e cada horário foi convertido para Brasília pelo fuso do município.
- O exterior fica de fora porque lá a urna registra a hora local de cada país.
- O log não diz em quem foi cada voto, porque o voto é secreto. Por isso não há divisão por candidato em cada horário.

Detalhes por UF e por seção: [`resultados/resumo.md`](resultados/resumo.md), [`resultados/votos_por_faixa.csv`](resultados/votos_por_faixa.csv), [`resultados/horarios_secoes.csv`](resultados/horarios_secoes.csv).

## Como reproduzir

Requisitos: Python 3.11+ e `curl`. Os scripts principais usam só a biblioteca padrão.

O repositório já traz `saida/`, com os dados extraídos de todas as seções. Para refazer só as comparações,
basta rodar `python compara.py`, que leva uns 4 minutos. Para refazer tudo a partir dos arquivos do TSE, apague
`saida/` antes, porque `processa.py` pula as UFs que já estão lá.

```bash
python processa.py demo                # autoteste da leitura de log e BU
python teste_assinatura.py             # autoteste da assinatura digital (seções reais em amostra/ e adulterações)
python processa.py                     # baixa ~115 GB do TSE, uma UF por vez, e apaga cada zip depois de extrair
python compara.py                      # baixa o resultado oficial e gera resultados/
```

Para retomar uma execução interrompida, rode `processa.py` de novo: as UFs já feitas são puladas. Para rodar
só algumas UFs, use `python processa.py AC AL`. Num computador com 8 núcleos, a execução completa levou 4h45min, e o download foi o gargalo.

Para conferir se você baixou os mesmos arquivos: `saida/zips/<UF>.sha256` e `resultados/oficial.sha256` trazem
o SHA-256 de cada arquivo do TSE usado.

## Os scripts

| arquivo | o que faz |
|---|---|
| `processa.py` | Para cada seção, extrai fatos sem interpretar. Do BU impresso tira aptos, comparecimento, horários e votos por candidato. Do log tira os votos por hora **local**. Também confere a assinatura digital. Grava `saida/`. |
| `assinatura.py` | Valida o arquivo de assinatura da urna só com a biblioteca padrão: leitor DER, Ed521 e ECDSA P-521. |
| `compara.py` | Aplica as regras (fusos, 17h/19h) e faz todas as comparações. Grava `resultados/`. |
| `confere_com_tse.py` | Valida 1% das seções com o **código de referência do próprio TSE** e mostra que ele concorda com `assinatura.py`. |

Separar extração de interpretação é proposital. As regras ficam todas em `compara.py`, então podem ser revistas sem baixar tudo de novo.

## Método e decisões

**Assinatura digital.** O arquivo `-vota.vsc` de cada seção tem duas assinaturas:

- **Software (algoritmo CEPESC):** o algoritmo não é público, então dela conferimos apenas os hashes.
- **Hardware (da própria urna):** é verificada por completo.
  - Ela é ECDSA P-521 nas urnas UE2013/UE2015 e Ed521 (padrão ICP-Brasil, curva E-521) nas UE2020/UE2022.
  - O certificado da urna precisa ser assinado por uma das ACs do TSE em [`acs/`](acs/). Esses certificados foram extraídos do pacote oficial
    `formato-arquivos-bu-rdv-ass-digital-v2.zip`, SHA-256 `1e423054f32b8ba056960c58ada167d702c2618cc4d1dfd5de88f5090c84a235`.

A implementação segue `python/assinatura_hash.py` e `python/lib/mr_util.py` desse pacote. O layout do arquivo de 2026 difere da especificação v2 publicada em dois pontos: o modelo da urna vem no final, e os campos opcionais usam tags `[0]` e `[1]`. A diferença está documentada em [`spec/assinatura-2026.diff`](spec/assinatura-2026.diff).

**Conferência cruzada com o código do TSE.** `processa.py` guarda em `amostra_tse/` os arquivos de 1% das seções, escolhidas pelo SHA-256 do nome da seção (critério fixo e reproduzível). `confere_com_tse.py` valida essas seções com o código do TSE e compara o resultado com o de `assinatura.py`.

Para rodar a conferência, instale as dependências que o próprio TSE indica. O ECPy precisa vir do git, porque não há release com Ed521:

```bash
pip install asn1tools pyopenssl "git+https://github.com/cslashm/ECPy.git@8143d9ac017de0cb7f980bedaf56cefe6b4d9180"
unzip tse-ref/formato-arquivos-bu-rdv-ass-digital-v2.zip -d tse-ref/pkg
python confere_com_tse.py amostra_tse/SP     # uma pasta por UF
```

**Votos no log.** Cada voto gera a linha `O voto do eleitor foi computado`. Só contamos as linhas de 25/10/2026, porque o log da urna também traz o 1º turno. Quando a urna foi substituída durante a votação, o log da urna anterior vem aninhado no pacote e também é contado. Sem isso, o log fica com menos votos que o BU.

**Fusos.** A votação abriu às 8h de Brasília no país todo, e a urna registra o horário local. O fuso de cada município é a hora de abertura mais comum entre as suas seções, menos 8.

- Esse critério dispensa uma tabela de municípios, que a lei não traz: o Decreto 2.784/1913, com a redação da Lei 12.876/2013, define o fuso por uma linha geográfica entre Tabatinga e Porto Acre.
- O critério é conferível: [`resultados/fusos_municipios.csv`](resultados/fusos_municipios.csv) lista o fuso deduzido de cada município, quantas seções concordam e se ele difere do padrão da UF. Os diferentes esperados são o oeste do Amazonas, com 2h a menos que Brasília, e Fernando de Noronha, com 1h a mais.
- No exterior (ZZ), a votação segue o horário local de cada país, e não convertemos para Brasília.

**17h e 19h.** O limite é contado a partir de 17h00min00s e de 19h00min00s de Brasília, inclusive. Como os fusos são horas inteiras, basta somar os votos por hora local. Votar depois do limite não é, por si só, irregular: quem estava na fila no encerramento recebe senha e vota. A decisão de prorrogação valeu só para as seções que ainda estavam abertas.

**BU.** Os números vêm do BU impresso (`imgbu.dat`), que também é assinado.

- Em cada cargo vale: candidatos + brancos + nulos = total apurado.
- Para presidente, o apurado é igual ao comparecimento.
- Para governador, o apurado pode ser menor: o eleitor em trânsito de outra UF vota só para presidente.

## Limitações

- **Assinatura de software (CEPESC):** não é verificável publicamente.
- **Arquivos não publicados:** o TSE não publica todos os arquivos que a urna assina (`jufa.dat`, `hash.dat`, `wsq*.jez`, `mr.ver`, `imgze.dat`). Eles aparecem em `assinados_nao_publicados`.
- **Cadeia de certificação:** termina nas ACs intermediárias publicadas no pacote do TSE (AC URNA, AC UE2020, AC UE2022). Os certificados raiz não estão disponíveis publicamente para download automatizado.
- **Cargos extras:** o BU também traz uma eleição para prefeito e uma consulta popular em MT, realizadas no mesmo dia. O resultado oficial por seção usado não cobre esses cargos, então eles aparecem nos totais, mas não são conferidos.
- **Exterior em cédula:** nas 29 seções do exterior apuradas em cédula (Sistema de Apuração), não há comparecimento nem votos no log para comparar.
- **RDV:** o RDV é baixado e tem hash e assinatura conferidos, mas ainda não é recontado.

## Licença

MIT. Ver [`LICENSE`](LICENSE).
