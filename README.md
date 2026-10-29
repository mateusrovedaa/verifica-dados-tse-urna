# Auditoria dos arquivos de urna — Eleições 2026, 2º turno

Auditoria independente e reprodutível dos arquivos que o TSE publica para cada seção eleitoral do 2º turno
de 25/10/2026: boletim de urna (BU), registro digital do voto (RDV), log da urna e arquivo de assinatura digital.

As perguntas:

1. **Os arquivos publicados estão íntegros?** O certificado de cada urna foi emitido por uma das autoridades
   certificadoras do TSE, e cada arquivo tem hash e assinatura da urna válidos.
2. **Log, RDV e BU contam a mesma coisa?** Os votos do log batem com o comparecimento do BU, e a recontagem
   do RDV, voto a voto, dá os totais do BU.
3. **O BU fecha por dentro?** Em cada cargo, candidatos + brancos + nulos = total apurado.
4. **Os BUs somam o resultado oficial?** Os votos de cada seção conferem com o resultado oficial por seção do TSE.
5. **Quantos votos foram dados depois das 17h e das 19h (horário de Brasília)?** O min. Cristiano Zanin
   (STF, Rcl 101.673) prorrogou a votação até 19h e depois restringiu a prorrogação às seções ainda abertas.

Cada divergência encontrada foi investigada em [`resultados/casos_investigados.md`](resultados/casos_investigados.md).
Os números completos estão em [`resultados/resumo.md`](resultados/resumo.md).

## Resultado em uma página

Nas 499.207 seções (Brasil e exterior):

- **Hashes e assinaturas da urna:** nenhuma falha. Uma amostra de 1% (5.011 seções) passou também pelo código do próprio TSE, com o mesmo resultado. Isso mostra que os arquivos não foram alterados depois de assinados pela urna. Se o software da urna estava correto é outra pergunta, que esta auditoria não responde (ver [Assinatura de software](#assinatura-de-software-cepesc)).
- **RDV:** a recontagem do RDV, voto a voto, dá exatamente os votos do BU para presidente e governador nas 499.205 seções que têm RDV. As 2 sem RDV são as seções do exterior que também faltam no resultado oficial e não têm votos para presidente. Na amostra de 1%, a leitura do RDV com a especificação do TSE dá a mesma contagem.
- **Resultado oficial:** para presidente e governador, os votos de cada boletim de urna são iguais aos do resultado oficial por seção do TSE. Ficam de fora 2 seções do exterior apuradas em cédula, que não aparecem no arquivo oficial.
- **Log x BU:** o log tem 127.854.309 votos no Brasil, 322 a menos que o comparecimento dos BUs (127.854.631), diferença de 0,0003%. A diferença está em 7 seções onde o log tem menos votos que o BU; em nenhuma seção o log tem mais (ver [casos investigados](resultados/casos_investigados.md)).

### Comparação com o resultado oficial do TSE

Soma dos boletins de urna publicados x resultado oficial por seção do TSE ([`votacao_secao_2026_BR.zip`](https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_BR.zip)):

| Presidente (Brasil + exterior) | Boletins de urna | Resultado oficial TSE | Diferença |
|---|---:|---:|---:|
| Lula (13) | 64.256.232 | 64.256.232 | 0 |
| Flávio Bolsonaro (22) | 59.826.041 | 59.826.041 | 0 |
| Brancos | 1.430.496 | 1.430.496 | 0 |
| Nulos | 2.723.305 | 2.723.305 | 0 |
| **Total** | **128.236.074** | **128.236.074** | **0** |

Nos votos válidos, Lula teve 51,79% e Flávio Bolsonaro, 48,21%.

Governador teve 2º turno em AC, AM, DF, ES, RN e TO. Os boletins de urna somam 10.086.066 votos para
governador, o mesmo número do resultado oficial, e cada candidato também confere (tabela em
[`resultados/resumo.md`](resultados/resumo.md)). Como a comparação é feita seção por seção, os totais por UF
e por município também batem.

### Votos por horário (Brasília, só Brasil)

| horário | votos | % dos votos do dia | seções com voto no horário |
|---|---:|---:|---:|
| 8h às 12h | 76.971.693 | 60,20% | 497.895 |
| 12h às 17h | 50.848.286 | 39,77% | 497.770 |
| 17h às 18h | 32.337 | 0,025% | 28.783 |
| 18h às 19h | 1.982 | 0,002% | 1.662 |
| **17h em diante¹** | **34.330** | **0,027%** | **29.854** |
| **Total** | **127.854.309** | **100%** | **497.897** |

¹ Inclui 11 votos depois das 19h: um em cada uma de 11 seções, na BA (2), no RJ (4) e em SP (5).

A tabela conta as linhas "O voto do eleitor foi computado" do log, porque só o log registra a hora de cada
voto (com hora, minuto e segundo). O total fica 322 votos (0,0003%) abaixo do comparecimento dos BUs, por causa das 7 seções com log incompleto descritas nas [limitações](#limitações). A urna grava a hora local, que convertemos para
Brasília pelo fuso do município. O exterior fica de fora porque lá a urna marca a hora de cada país. O voto
é secreto e o log não diz em quem foi cada voto, por isso não há divisão por candidato em cada horário.

Por seção e por UF: [`resultados/votos_por_faixa.csv`](resultados/votos_por_faixa.csv), [`resultados/horarios_secoes.csv`](resultados/horarios_secoes.csv) e [`resultados/resumo.md`](resultados/resumo.md).

## Como reproduzir

Requisitos: Python 3.11+ e `curl`. Os scripts principais usam só a biblioteca padrão.

O repositório já traz `saida/`, com os dados extraídos de todas as seções. Para refazer só as comparações,
rode `python compara.py` (uns 4 minutos). Para refazer tudo a partir dos arquivos do TSE, apague `saida/`
antes, porque `processa.py` pula as UFs que já estão lá.

```bash
python processa.py demo                # autoteste da leitura de log, RDV e BU
python teste_assinatura.py             # autoteste da assinatura digital (seções reais em amostra/ e adulterações)
python processa.py                     # baixa ~115 GB do TSE, uma UF por vez, e apaga cada zip depois de extrair
python compara.py                      # baixa o resultado oficial e gera resultados/
```

Para retomar uma execução interrompida, rode `processa.py` de novo, e as UFs já feitas são puladas. Para
rodar só algumas UFs, use `python processa.py AC AL`. Num computador com 8 núcleos, a execução completa
levou cerca de 4 horas, e o gargalo foi o download.

[`hashes_tse/`](hashes_tse/) guarda o SHA-256 de cada arquivo do TSE usado nesta auditoria. Se o TSE trocar
um arquivo, `processa.py` e `compara.py` param com erro em vez de gerar outros números.

Para ver os arquivos de uma seção sem baixar o zip da UF inteiro:

```bash
python baixa_secao.py o03221es5793200090085     # grava em secoes/<seção>/
```

## Os scripts

| arquivo | o que faz |
|---|---|
| `processa.py` | Extrai os dados de cada seção, sem interpretar. Do BU impresso tira aptos, comparecimento, horários e votos por candidato. Do log tira os votos por hora **local**. Reconta o RDV e confere a assinatura digital. Grava `saida/`. |
| `assinatura.py` | Valida o arquivo de assinatura da urna só com a biblioteca padrão: leitor DER, certificados, Ed521 e ECDSA P-521. |
| `compara.py` | Aplica as regras (fusos, 17h/19h) e faz todas as comparações. Grava `resultados/`. |
| `confere_com_tse.py` | Confere `assinatura.py` e a recontagem do RDV com o **código e a especificação do próprio TSE** em 1% das seções, e testa o verificador com assinaturas geradas por outras bibliotecas. |
| `baixa_secao.py` | Baixa os arquivos de uma seção direto do zip do TSE, para conferência manual. |

As regras de interpretação ficam todas em `compara.py`, separadas da extração, para que possam ser revistas sem baixar tudo de novo.

## Método e decisões

**Assinatura digital.** O arquivo `-vota.vsc` de cada seção tem duas assinaturas:

- **Software (algoritmo CEPESC):** dela conferimos só os hashes. Ver [Assinatura de software](#assinatura-de-software-cepesc).
- **Hardware (da própria urna):** verificada por completo.
  - O algoritmo é ECDSA P-521 nas urnas UE2013/UE2015 e Ed521 (padrão ICP-Brasil, curva E-521) nas UE2020/UE2022.
  - O certificado da urna precisa ter sido emitido e assinado por uma das ACs do TSE em [`acs/`](acs/), e estar dentro da validade em 25/10/2026. Os certificados das ACs vêm do pacote oficial
    `formato-arquivos-bu-rdv-ass-digital-v2.zip`, SHA-256 `1e423054f32b8ba056960c58ada167d702c2618cc4d1dfd5de88f5090c84a235`.

A implementação segue `python/assinatura_hash.py` e `python/lib/mr_util.py` desse pacote. O arquivo de 2026 difere da especificação v2 publicada em dois pontos: o modelo da urna vem no final, e os campos opcionais usam tags `[0]` e `[1]`. A diferença está em [`spec/assinatura-2026.diff`](spec/assinatura-2026.diff).

Além do que o código do TSE confere, `assinatura.py` recusa DER truncado ou com comprimento indefinido e chaves Ed521 fora do subgrupo de ordem prima (pontos de ordem pequena).

**Conferência cruzada.** `processa.py` guarda em `amostra_tse/` os arquivos de 1% das seções, escolhidas pelo SHA-256 do nome da seção (critério fixo e reproduzível). `confere_com_tse.py` faz três coisas:

1. valida essas seções com o código do TSE e compara com `assinatura.py`;
2. decodifica cada RDV com a especificação ASN.1 do TSE e compara com a recontagem de `processa.py`;
3. gera assinaturas Ed521 com o ECPy (a biblioteca que o TSE usa) e ECDSA P-521 com o OpenSSL, e confere que `assinatura.py` aceita as válidas e recusa as adulteradas.

Para rodar, instale as dependências que o próprio TSE indica. O ECPy precisa vir do git, porque nenhuma versão publicada tem Ed521:

```bash
pip install asn1tools pyopenssl "git+https://github.com/cslashm/ECPy.git@8143d9ac017de0cb7f980bedaf56cefe6b4d9180"
unzip tse-ref/formato-arquivos-bu-rdv-ass-digital-v2.zip -d tse-ref/pkg
python confere_com_tse.py amostra_tse/SP     # uma pasta por UF
```

**RDV.** O RDV guarda cada voto da seção, embaralhado, no formato `spec/rdv.asn1` do pacote do TSE. `processa.py` conta os votos de cada cargo: nominal pelo número digitado, branco e nulo pelos tipos de voto. `compara.py` confere essa contagem com o BU para presidente e governador.

**Votos no log.** Contamos as linhas `O voto do eleitor foi computado` de 25/10/2026 (o log também traz o 1º turno). A urna grava essa linha a cada voto, salvo quando reinicia logo depois de um (ver [casos investigados](resultados/casos_investigados.md)). Quando a urna foi trocada durante a votação, o log da anterior vem aninhado no pacote e também entra na conta. Alguns pacotes do TSE trazem logs a mais, então aplicamos duas regras:

- um log aninhado que só declara outra seção ("Seção Eleitoral: NNNN") é ignorado;
- linhas de voto idênticas (mesmo horário, urna e código de verificação) contam uma vez.

O que essas regras ignoram fica registrado por seção, nas colunas `logs_outra_secao_ignorados` e `linhas_voto_repetidas_ignoradas` de `saida/secoes/`.

**Fusos.** A votação abriu às 8h de Brasília no país todo, e a urna registra o horário local. O fuso de cada município é a hora de abertura mais comum entre as suas seções, menos 8.

- A lei não traz uma tabela de municípios: o Decreto 2.784/1913, com a redação da Lei 12.876/2013, define o fuso por uma linha geográfica entre Tabatinga e Porto Acre. Este critério dispensa a tabela.
- [`resultados/fusos_municipios.csv`](resultados/fusos_municipios.csv) lista o fuso deduzido de cada município, quantas seções concordam e se ele difere do padrão da UF. Nos 5.571 municípios, o fuso deduzido é igual ao padrão da UF, com 12 exceções, que são as previstas: 11 municípios do oeste do Amazonas, 2h atrás de Brasília, e Fernando de Noronha, 1h à frente. Em cada uma das 12, todas as seções concordam. Onde alguma seção discorda, ela abriu atrasada, e a maioria define o fuso.
- No exterior (ZZ), a votação segue o horário local de cada país, e não convertemos para Brasília.

**17h e 19h.** Os limites contam a partir de 17h00min00s e de 19h00min00s de Brasília, inclusive. Como os fusos são horas inteiras, basta somar os votos por hora local. Quem estava na fila no encerramento recebe senha e vota, então votos depois do limite são esperados. A prorrogação valeu só para as seções que ainda estavam abertas.

**BU.** Os números vêm do BU impresso (`imgbu.dat`), que também é assinado.

- Em cada cargo, candidatos + brancos + nulos = total apurado.
- Para presidente, o apurado é igual ao comparecimento.
- Para governador, o apurado pode ser menor, porque o eleitor em trânsito de outra UF vota só para presidente.

## Assinatura de software (CEPESC)

Cada arquivo leva duas assinaturas. A da própria urna (hardware) é verificada por completo nesta auditoria.
A segunda, feita pelo software de votação, usa um algoritmo do **CEPESC**, o Centro de Pesquisa e
Desenvolvimento para a Segurança das Comunicações, ligado à Agência Brasileira de Inteligência (ABIN). O
algoritmo é sigiloso, então dessa assinatura conferimos os hashes (SHA-512) dos arquivos listados nela, e
todos batem.

Esta auditoria confere os arquivos que o TSE publica depois da eleição. Duas outras perguntas são
respondidas antes e durante a votação, em etapas públicas e com resultado divulgado: se o software
instalado nas urnas é o mesmo que foi inspecionado e se ele registra os votos corretamente. Qualquer
pessoa pode acompanhar ou consultar cada etapa:

| etapa | quando (2026) | como funciona | resultado |
|---|---|---|---|
| [Inspeção do código-fonte](https://www.tse.jus.br/comunicacao/noticias/2025/Novembro/codigos-fonte-do-ciclo-de-transparencia-ao-teste-publico-da-urna) | de 2/10/2025 até a lacração | Partidos, federações, OAB, Ministério Público, Polícia Federal, CGU, SBC e outras entidades leem o código-fonte da urna e dos sistemas na sede do TSE ([Resolução TSE nº 23.673/2021](https://www.tse.jus.br/legislacao/compilada/res/2021/resolucao-no-23-673-14-de-dezembro-de-2021)). | — |
| [Teste Público da Urna](https://www.tse.jus.br/eleicoes/tpu) | 1º a 5/12/2025, confirmação de 13 a 15/5/2026 | Qualquer brasileiro maior de 18 anos pode se inscrever e tentar atacar a urna e os sistemas. Os achados são corrigidos e testados de novo no teste de confirmação. | nenhum achado comprometeu a integridade ou o sigilo do voto ([teste de confirmação](https://www.tse.jus.br/comunicacao/noticias/2026/Maio/tse-realiza-teste-de-confirmacao-do-teste-publico-da-urna-de-13-a-15-de-maio)) |
| [Assinatura digital e lacração dos sistemas](https://www.tse.jus.br/comunicacao/noticias/2026/Setembro/sistemas-das-eleicoes-gerais-de-2026-sao-assinados-digitalmente-e-lacrados-pelo-tse) | 4/9/2026 | O TSE e entidades fiscalizadoras (entre elas PF e OAB) assinam os resumos digitais (hashes) dos programas inspecionados. As mídias ficam lacradas na Sala Cofre do TSE. | sistemas congelados |
| [Verificação dos sistemas na véspera](https://www.tse.jus.br/comunicacao/noticias/2026/Outubro/tse-verifica-os-sistemas-eleitorais-na-vespera-do-2o-turno-das-eleicoes-2026) | 24/10/2026 | Os sistemas instalados têm as assinaturas e os resumos digitais comparados com os lacrados. | conferem |
| [Teste de Integridade](https://www.tse.jus.br/comunicacao/noticias/2026/Outubro/teste-de-integridade-do-2o-turno-no-tse-confirma-correspondencia-entre-cedulas-e-votos-nas-urnas) | 25/10/2026, durante a votação | Urnas sorteadas na véspera saem das seções e recebem, em paralelo à eleição, votos de cédulas de papel preenchidas antes. No fim, o BU de cada urna é comparado com a contagem das cédulas. Acontece nas 26 capitais e no DF, filmado e transmitido ao vivo pelo canal do TSE no YouTube. | no TSE, 389 votos auditados, sem divergência entre cédulas e urnas |

A Resolução TSE nº 23.758/2026 prevê um relatório consolidado do Teste de Integridade de todos os TREs em
até 90 dias após o 2º turno ([texto](https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-758-de-2-de-marco-de-2026)).

O BU impresso de cada seção também é afixado no local de votação ao fim do dia e traz um QR code. Quem
fotografou um BU pode compará-lo com o publicado: os números desta auditoria saem desses mesmos BUs, e eles
conferem com o resultado oficial.

## Limitações

- **Assinatura de software (CEPESC):** o algoritmo é sigiloso, então essa assinatura não é verificável fora do TSE; conferimos os hashes listados nela. Impacto: o funcionamento do software não é objeto desta auditoria, e sim das etapas públicas descritas [acima](#assinatura-de-software-cepesc), entre elas o Teste de Integridade do 2º turno, que não encontrou divergência entre cédulas e urnas.
- **Arquivos não publicados:** o TSE não publica todos os arquivos que a urna assina (`jufa.dat`, `hash.dat`, `wsq*.jez`, `mr.ver`, `imgze.dat`). Eles aparecem em `assinados_nao_publicados`. Impacto: nenhum nos números, porque o que se compara (BU, RDV, log e resultado oficial) é publicado; fica sem conferência, por exemplo, a zerésima (`imgze.dat`), que mostraria a urna vazia antes da votação.
- **Cadeia de certificação:** conferimos que o certificado de cada urna foi emitido e assinado por uma das ACs publicadas no pacote do TSE (AC URNA, AC UE2020, AC UE2022) e que estava dentro da validade em 25/10/2026. A raiz, as extensões e a revogação não foram verificadas, porque esses certificados e listas não são públicos. Impacto: baixo; se a chave de uma AC tivesse vazado ou o certificado de uma urna tivesse sido revogado, não saberíamos, mas as chaves usadas são as do pacote oficial do TSE, com SHA-256 registrado.
- **Log incompleto em algumas seções:** em 7 seções o log tem menos votos que o BU, 322 no total: uma seção de SP sem log publicado (268), duas urnas substituídas cujo log de 25/10 não veio no pacote (BA, 13; MA, 36), uma urna substituída no RS (2) e três urnas que reiniciaram logo depois de um voto, sem gravar a linha de voto computado (1 cada, em BA, PB e PI). Impacto: a tabela por horário fica com 322 votos a menos (0,0003%), sem hora conhecida; mesmo que todos fossem depois das 17h, a faixa passaria de 34.330 para 34.652. Os totais de presidente e governador não usam o log e não mudam.
- **Cargos extras:** o BU também traz uma eleição para prefeito e uma consulta popular em MT, realizadas no mesmo dia. O resultado oficial por seção usado não cobre esses cargos, então eles aparecem nos totais, mas não são conferidos. Impacto: nenhum em presidente e governador, porque prefeito e a consulta em MT só passam pelas conferências internas do BU.
- **Exterior em cédula:** nas 29 seções do exterior apuradas em cédula (Sistema de Apuração), não há comparecimento nem votos no log para comparar. Impacto: 831 votos para presidente (0,0006% do total), que são conferidos só contra o resultado oficial, e batem; as 2 seções do exterior que faltam no resultado oficial não têm votos para presidente.

## Licença

MIT. Ver [`LICENSE`](LICENSE).
