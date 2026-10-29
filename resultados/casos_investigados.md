# Casos investigados

Todas as divergências de `divergencias.csv` foram abertas uma a uma. Os arquivos de cada seção podem ser
baixados de novo do zip do TSE com `python baixa_secao.py <seção>`, que lê só os trechos necessários
(HTTP Range). Nenhum caso afeta os totais de presidente e governador, que batem voto a voto com o resultado
oficial e com a recontagem do RDV. As 7 seções com log incompleto deixam o total do log 322 votos abaixo do
comparecimento dos BUs no Brasil (0,0003%).

## Assinatura digital

As 499.207 seções têm certificado de urna emitido por uma AC do TSE:

| AC | seções |
|---|---|
| AC URNA | 99.957 |
| AC UE2020 | 200.504 |
| AC UE2022 | 198.746 |

Em nenhuma seção houve falha de hash ou de assinatura.

## Cargos não conferidos (3.204 seções)

O BU traz também uma eleição para **prefeito** e uma consulta popular (**Desmembramento de Nova Poxoréu**, MT),
realizadas no mesmo dia. O resultado oficial por seção usado aqui (`votacao_secao_2026_*.zip`) cobre só
presidente e governador. Esses dois cargos extras aparecem nos totais de `resumo.md` como "não conferido".

## 29 seções do exterior apuradas em cédula

São as 27 linhas "BU inconsistente" e as 29 "BU impresso sem comparecimento", todas no exterior (ZZ).
Nessas seções, o BU é `imgbusa.dat`, gerado pelo **Sistema de Apuração** a partir de cédulas, e o log é
`logsa.jez`. Esse BU não tem linha de comparecimento, então a regra "presidente apurado = comparecimento"
não se aplica. Em todas essas seções, candidatos + brancos + nulos = total apurado.

Duas dessas seções (`o03221zz2956400010091` e `o03221zz3068600010443`) não aparecem no resultado oficial por seção.

## Três pacotes com log a mais (corrigido pelas regras de contagem)

Nesses pacotes, somar todos os logs dava mais votos que o BU. As duas regras de `processa.py` (ignorar log
aninhado que só declara outra seção; contar uma vez linhas de voto idênticas) deixam o log igual ao BU:

| seção | log sem as regras | log com as regras | BU | o que havia a mais no pacote |
|---|---|---|---|---|
| `o03221es5793200090085` | 612 | 308 | 308 | o log da urna de outra seção (0112, 304 votos) |
| `o03221ba3987001330184` | 413 | 228 | 228 | o log da urna substituída duas vezes (185 + 185), mais 43 votos na urna de contingência |
| `o03221mg4069000160264` | 160 | 114 | 114 | uma cópia parcial do log da primeira urna (46), além do log que já junta as duas urnas (114) |

O que foi ignorado fica registrado nas colunas `logs_outra_secao_ignorados` e
`linhas_voto_repetidas_ignoradas` de `saida/secoes/`.

## Sete seções com log menor que o BU

| seção | log | BU | causa |
|---|---|---|---|
| `o03221sp6477703950298` | 0 | 268 | O zip de SP traz o BU, o RDV e a assinatura dessa seção, mas não o `log.jez`. |
| `o03221ma0889300470609` | 188 | 224 | A urna substituída não tem log de 25/10 no pacote: seu log aninhado só traz votos do 1º turno. Os 36 votos dados nela antes da troca aparecem só no BU. |
| `o03221ba3565301730235` | 204 | 217 | Mesma situação, com 13 votos. |
| `o03221rs8906000170191` | 90 | 92 | Urna substituída. Um voto é um reinício como os da linha seguinte; o outro não aparece no log. |
| `o03221pb2175000020254` | 303 | 304 | A urna reiniciou logo após um voto: há 304 linhas "Voto confirmado para [Presidente]", mas só 303 linhas "O voto do eleitor foi computado". |
| `o03221pi1153300030216` | 258 | 259 | Idem (259 confirmados). |
| `o03221ba3471100210178` | 233 | 234 | Idem (234 confirmados). |

Em todas, o BU e o RDV conferem entre si e com o resultado oficial. Os 322 votos sem linha no log ficam fora
da tabela por horário, porque não têm hora registrada.

## Arquivos fora do padrão nos zips

Dezenove UFs trazem arquivos `.id` fora do padrão de nomes de seção (lista em `saida/extras/`). Abrimos
`se0-sdjkADYayq-9IGAwt7Kc4ewW+hrQ09v-buq4S84=.id` (AP): ele tem 47 bytes e o conteúdo é o próprio nome do
arquivo. Não há dado de seção. Fora esses, os extras são apenas `leiame.pdf`.
