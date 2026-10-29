# Auditoria dos arquivos de urna — Eleições 2026, 2º turno

Auditoria independente e reprodutível dos arquivos que o TSE publica para cada seção eleitoral do 2º turno
de 25/10/2026: boletim de urna (BU), registro digital do voto (RDV), log da urna e arquivo de assinatura digital.

As perguntas respondidas:

1. **Os arquivos publicados estão íntegros?** O certificado de cada urna foi assinado por uma das autoridades
   certificadoras do TSE, e cada arquivo publicado tem hash e assinatura da urna válidos.
2. **Log e BU contam a mesma coisa?** Os votos registrados no log de cada urna batem com o comparecimento do BU.
3. **O BU fecha por dentro?** Em cada cargo, candidatos + brancos + nulos = total apurado.
4. **Os BUs somam o resultado oficial?** Os votos de cada seção conferem com o resultado oficial por seção publicado pelo TSE.
5. **Quantos votos foram dados depois das 17h e das 19h (horário de Brasília)?** O horário foi prorrogado até 19h
   pela decisão do min. Cristiano Zanin (STF, Rcl 101.673), depois restrita às seções ainda abertas.

Resultados: [`resultados/resumo.md`](resultados/resumo.md). Cada divergência encontrada foi investigada em
[`resultados/casos_investigados.md`](resultados/casos_investigados.md).

## Resultado em uma página

Nas 499.207 seções (Brasil e exterior):

- **Hashes e assinaturas da urna:** sem nenhuma falha. Uma amostra de 1% (5.011 seções) foi validada também com o código do próprio TSE, e o resultado foi o mesmo. Isso mostra que os arquivos não foram alterados depois de assinados pela urna. Não mostra que o software da urna estava correto (ver [Limitações](#limitações)).
- **Resultado oficial:** para presidente e governador, os votos de cada boletim de urna são iguais aos do resultado oficial por seção do TSE. A exceção são 2 seções do exterior apuradas em cédula, que não aparecem no arquivo oficial.
- **Log x BU:** os votos registrados no log batem com o boletim em todas as seções, menos 10. As causas estão em [casos_investigados.md](resultados/casos_investigados.md): logs duplicados ou de outra seção no pacote, urnas substituídas, reinício da urna logo após um voto e uma seção sem log publicado.

### Comparação com o resultado oficial do TSE

Soma dos boletins de urna publicados x resultado oficial por seção do TSE ([`votacao_secao_2026_BR.zip`](https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_BR.zip)):

| Presidente (Brasil + exterior) | Boletins de urna | Resultado oficial TSE | Diferença |
|---|---:|---:|---:|
| Lula (13) | 64.256.232 | 64.256.232 | 0 |
| Flávio Bolsonaro (22) | 59.826.041 | 59.826.041 | 0 |
| Brancos | 1.430.496 | 1.430.496 | 0 |
| Nulos | 2.723.305 | 2.723.305 | 0 |
| **Total** | **128.236.074** | **128.236.074** | **0** |

- **Votos válidos:** Lula 51,79% e Flávio Bolsonaro 48,21%.
- **Governador:** teve 2º turno em AC, AM, DF, ES, RN e TO. A soma de todos os votos para governador é 10.086.066 nos boletins de urna e 10.086.066 no resultado oficial, e cada candidato também confere. A tabela por candidato está em [`resultados/resumo.md`](resultados/resumo.md).
- **Como foi feita:** a comparação é seção por seção, então os totais por UF e por município também batem.

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

- A tabela conta as linhas "O voto do eleitor foi computado" do log, porque é o log que registra a hora de cada voto.
  O total, 127.854.844, fica 213 acima do comparecimento dos BUs no Brasil (127.854.631), uma diferença de 0,0002%.
  Ela vem das 10 seções de [casos_investigados.md](resultados/casos_investigados.md) e não atinge a faixa a partir das 17h.
- Os horários vêm do log de cada urna, que registra cada voto com hora, minuto e segundo. O log grava a hora local, e cada horário foi convertido para Brasília pelo fuso do município.
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

**Votos no log.** Contamos as linhas `O voto do eleitor foi computado`, que a urna grava a cada voto. A exceção é quando ela reinicia logo depois do voto (ver [casos investigados](resultados/casos_investigados.md)). Só contamos as linhas de 25/10/2026, porque o log da urna também traz o 1º turno. Quando a urna foi substituída durante a votação, o log da urna anterior vem aninhado no pacote e também é contado. Sem isso, o log fica com menos votos que o BU.

**Fusos.** A votação abriu às 8h de Brasília no país todo, e a urna registra o horário local. O fuso de cada município é a hora de abertura mais comum entre as suas seções, menos 8.

- Esse critério dispensa uma tabela de municípios, que a lei não traz: o Decreto 2.784/1913, com a redação da Lei 12.876/2013, define o fuso por uma linha geográfica entre Tabatinga e Porto Acre.
- O critério é conferível: [`resultados/fusos_municipios.csv`](resultados/fusos_municipios.csv) lista o fuso deduzido de cada município, quantas seções concordam e se ele difere do padrão da UF. Nos 5.571 municípios, o fuso deduzido é igual ao padrão da UF, com 12 exceções. São exatamente os casos previstos: 11 municípios do oeste do Amazonas, com 2h a menos que Brasília, e Fernando de Noronha, com 1h a mais. Em todas as 12 exceções, 100% das seções concordam. Nos municípios em que alguma seção discorda, a causa é uma abertura atrasada, e a maioria das seções define o fuso.
- No exterior (ZZ), a votação segue o horário local de cada país, e não convertemos para Brasília.

**17h e 19h.** O limite é contado a partir de 17h00min00s e de 19h00min00s de Brasília, inclusive. Como os fusos são horas inteiras, basta somar os votos por hora local. Votar depois do limite não é, por si só, irregular: quem estava na fila no encerramento recebe senha e vota. A decisão de prorrogação valeu só para as seções que ainda estavam abertas.

**BU.** Os números vêm do BU impresso (`imgbu.dat`), que também é assinado.

- Em cada cargo vale: candidatos + brancos + nulos = total apurado.
- Para presidente, o apurado é igual ao comparecimento.
- Para governador, o apurado pode ser menor: o eleitor em trânsito de outra UF vota só para presidente.

## Limitações

- **Assinatura de software (CEPESC):** não é verificável publicamente.
- **Arquivos não publicados:** o TSE não publica todos os arquivos que a urna assina (`jufa.dat`, `hash.dat`, `wsq*.jez`, `mr.ver`, `imgze.dat`). Eles aparecem em `assinados_nao_publicados`.
- **Cadeia de certificação:** a verificação confirma que o certificado de cada urna foi assinado por uma das ACs intermediárias publicadas no pacote do TSE (AC URNA, AC UE2020, AC UE2022). Não verificamos a raiz, as datas de validade, as extensões nem a revogação.
- **Verificador próprio:** `assinatura.py` foi escrito para os arquivos reais do TSE e concorda com o código do TSE, mas não foi testado contra entradas forjadas de propósito: DER malformado, pontos de ordem pequena em Ed521 etc.
- **Fonte pode mudar:** os SHA-256 dos zips do TSE ficam registrados em `saida/zips/` e `resultados/oficial.sha256`, mas os scripts não interrompem a execução se um arquivo mudar. A comparação com os hashes registrados é manual.
- **Casos investigados:** a inspeção manual das 10 seções baixou os arquivos de cada seção direto do zip do TSE. Esse passo não tem script no repositório.
- **Cargos extras:** o BU também traz uma eleição para prefeito e uma consulta popular em MT, realizadas no mesmo dia. O resultado oficial por seção usado não cobre esses cargos, então eles aparecem nos totais, mas não são conferidos.
- **Contagem do log:** `processa.py` soma as linhas "O voto do eleitor foi computado" de todos os logs do pacote de cada seção, inclusive os aninhados. Isso é necessário para contar os votos de urnas substituídas durante a votação. Em 3 pacotes do TSE, porém, há logs que não deveriam ser somados:
  - em ES, o log de outra seção (+304);
  - em BA, uma cópia duplicada do log (+185);
  - em MG, um log que repete parte de outro (+46).

  São 535 votos a mais. No sentido contrário, faltam no log 322 votos que estão no BU: uma seção de SP sem log, urnas substituídas sem o log do dia e reinícios logo após um voto. Por isso, o total da tabela de horários fica 213 acima do comparecimento dos BUs. Os 535 a mais poderiam ser removidos com duas regras: contar uma só vez as linhas idênticas e ignorar logs de outra seção. Não as aplicamos, para manter a extração literal e deixar a falha dos pacotes visível. O efeito é de 0,0004% nas faixas antes das 17h e nenhum a partir das 17h. Os casos estão em [casos_investigados.md](resultados/casos_investigados.md).
- **Exterior em cédula:** nas 29 seções do exterior apuradas em cédula (Sistema de Apuração), não há comparecimento nem votos no log para comparar.
- **RDV:** o RDV é baixado e tem hash e assinatura conferidos, mas ainda não é recontado.

## Licença

MIT. Ver [`LICENSE`](LICENSE).
