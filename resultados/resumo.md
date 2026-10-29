# Auditoria dos arquivos de urna — 2º turno, 25/10/2026

- Seções com arquivos de urna: 499207 (AC, AL, AM, AP, BA, CE, DF, ES, GO, MA, MG, MS, MT, PA, PB, PE, PI, PR, RJ, RN, RO, RR, RS, SC, SE, SP, TO, ZZ)
- UFs não processadas: nenhuma
- Seções no resultado oficial: 499205
- Cargos sem resultado oficial por seção nos arquivos usados (não conferidos): DESMEMBRAMENTO DE NOVA POXORÉU, PREFEITO
- Municípios com fuso diferente do padrão da UF: 12 (ver fusos_municipios.csv)
- Seções com RDV recontado: 499205
- Seções com certificado de urna emitido pela acue2020: 200504
- Seções com certificado de urna emitido pela acue2022: 198746
- Seções com certificado de urna emitido pela acurna: 99957

## Divergências

| tipo | quantidade |
|---|---|
| problemas | 30 |
| BU inconsistente | 27 |
| votos no log diferente do comparecimento no BU | 7 |
| BU publicado sem seção no resultado oficial | 2 |

## Votos por horário (Brasília, sem exterior)

| UF | seções | votos | a partir das 17h | seções com voto ≥17h | a partir das 19h | seções com voto ≥19h |
|---|---|---|---|---|---|---|
| AC | 2270 | 453654 | 158 | 141 | 0 | 0 |
| AL | 7101 | 1951632 | 646 | 552 | 0 | 0 |
| AM | 8157 | 2192059 | 1004 | 879 | 0 | 0 |
| AP | 1914 | 429975 | 142 | 131 | 0 | 0 |
| BA | 35476 | 9422033 | 4190 | 3449 | 2 | 2 |
| CE | 23765 | 6024843 | 1074 | 960 | 0 | 0 |
| DF | 6969 | 1868280 | 980 | 876 | 0 | 0 |
| ES | 9844 | 2409214 | 294 | 269 | 0 | 0 |
| GO | 15686 | 4047280 | 734 | 643 | 0 | 0 |
| MA | 18093 | 4127735 | 921 | 828 | 0 | 0 |
| MG | 52062 | 13044203 | 2253 | 2084 | 0 | 0 |
| MS | 7106 | 1594460 | 422 | 388 | 0 | 0 |
| MT | 8287 | 2085334 | 909 | 797 | 0 | 0 |
| PA | 20827 | 4989573 | 1308 | 1173 | 0 | 0 |
| PB | 10712 | 2743559 | 471 | 416 | 0 | 0 |
| PE | 21418 | 6126467 | 1636 | 1436 | 0 | 0 |
| PI | 10225 | 2239829 | 337 | 299 | 0 | 0 |
| PR | 27142 | 7059339 | 926 | 877 | 0 | 0 |
| RJ | 37675 | 10077449 | 4150 | 3431 | 4 | 4 |
| RN | 8115 | 2232823 | 413 | 372 | 0 | 0 |
| RO | 4698 | 988489 | 555 | 496 | 0 | 0 |
| RR | 1519 | 308597 | 145 | 135 | 0 | 0 |
| RS | 27547 | 6889636 | 829 | 748 | 0 | 0 |
| SC | 17326 | 4762303 | 463 | 433 | 0 | 0 |
| SE | 5923 | 1466659 | 287 | 264 | 0 | 0 |
| SP | 103656 | 27364121 | 8860 | 7574 | 5 | 5 |
| TO | 4384 | 954763 | 223 | 203 | 0 | 0 |
| **Total** | 497897 | 127854309 | 34330 | 29854 | 11 | 11 |

## Votos por faixa de horário (Brasília, sem exterior)

| faixa | votos | % dos votos do dia | seções com voto na faixa |
|---|---|---|---|
| antes das 8h | 0 | 0.000% | 0 |
| 8h–12h | 76971693 | 60.203% | 497895 |
| 12h–17h | 50848286 | 39.770% | 497770 |
| 17h–18h | 32337 | 0.025% | 28783 |
| 18h–19h | 1982 | 0.002% | 1662 |
| a partir das 19h | 11 | 0.000% | 11 |
| a partir das 17h | 34330 | 0.027% | 29854 |

## Totais por candidato: BUs publicados x resultado oficial

| cargo | número | BUs | oficial | diferença |
|---|---|---|---|---|
| DESMEMBRAMENTO DE NOVA POXORÉU | 1 | 14116 | não conferido | |
| DESMEMBRAMENTO DE NOVA POXORÉU | 2 | 41590 | não conferido | |
| DESMEMBRAMENTO DE NOVA POXORÉU | BRANCO | 506 | não conferido | |
| DESMEMBRAMENTO DE NOVA POXORÉU | NULO | 287 | não conferido | |
| GOVERNADOR | 10 | 1290926 | 1290926 | 0 |
| GOVERNADOR | 11 | 1259777 | 1259777 | 0 |
| GOVERNADOR | 13 | 1812154 | 1812154 | 0 |
| GOVERNADOR | 15 | 1056119 | 1056119 | 0 |
| GOVERNADOR | 22 | 800328 | 800328 | 0 |
| GOVERNADOR | 44 | 1349475 | 1349475 | 0 |
| GOVERNADOR | 45 | 562083 | 562083 | 0 |
| GOVERNADOR | 55 | 1273975 | 1273975 | 0 |
| GOVERNADOR | BRANCO | 228427 | 228427 | 0 |
| GOVERNADOR | NULO | 452802 | 452802 | 0 |
| PREFEITO | 10 | 9 | não conferido | |
| PREFEITO | 11 | 2701 | não conferido | |
| PREFEITO | 12 | 58054 | não conferido | |
| PREFEITO | 13 | 4286 | não conferido | |
| PREFEITO | 15 | 6136 | não conferido | |
| PREFEITO | 20 | 3446 | não conferido | |
| PREFEITO | 25 | 1617 | não conferido | |
| PREFEITO | 30 | 14260 | não conferido | |
| PREFEITO | 35 | 380 | não conferido | |
| PREFEITO | 44 | 11736 | não conferido | |
| PREFEITO | 45 | 4166 | não conferido | |
| PREFEITO | 55 | 3553 | não conferido | |
| PREFEITO | 77 | 3863 | não conferido | |
| PREFEITO | BRANCO | 2408 | não conferido | |
| PREFEITO | NULO | 4175 | não conferido | |
| PRESIDENTE | 13 | 64256232 | 64256232 | 0 |
| PRESIDENTE | 22 | 59826041 | 59826041 | 0 |
| PRESIDENTE | BRANCO | 1430496 | 1430496 | 0 |
| PRESIDENTE | NULO | 2723305 | 2723305 | 0 |
