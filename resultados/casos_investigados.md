# Casos investigados

Todas as divergências de `divergencias.csv` foram abertas uma a uma. Para isso, os arquivos de cada seção
foram baixados de novo do zip do TSE, lendo só os trechos necessários (HTTP Range). Nenhum caso afeta os
totais de presidente e governador, que batem voto a voto com o resultado oficial, nem a contagem de votos a
partir das 17h. Os três pacotes com log a mais (abaixo) fazem o total de votos no log do Brasil ficar
213 acima do comparecimento dos BUs (0,0002%), nas faixas antes das 17h.

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

## Uma seção sem log publicado

`o03221sp6477703950298`: o zip de SP traz o BU, o RDV e a assinatura dessa seção, mas não traz o `log.jez`.
O BU confere com o resultado oficial.

## Nove seções com log diferente do BU

| seção | log | BU | causa |
|---|---|---|---|
| `o03221es5793200090085` | 612 | 308 | O pacote inclui o log da urna de **outra seção** (0112, 304 votos). A urna da própria seção registra 308. |
| `o03221ba3987001330184` | 413 | 228 | O log da urna substituída aparece **duas vezes** no pacote (185 + 185), mais 43 votos na urna de contingência. Sem a cópia: 185 + 43 = 228. |
| `o03221mg4069000160264` | 160 | 114 | Um log aninhado já junta as duas urnas (114). Outro traz uma cópia parcial da primeira urna (46). |
| `o03221ba3565301730235` | 204 | 217 | A urna substituída não tem log de 25/10 no pacote: seu log aninhado só traz votos do 1º turno. Os 13 votos dados nela antes da troca aparecem só no BU. |
| `o03221ma0889300470609` | 188 | 224 | Mesma situação, com 36 votos. |
| `o03221rs8906000170191` | 90 | 92 | Urna substituída. Um voto é o caso da linha seguinte, e o outro não aparece no log. |
| `o03221pb2175000020254` | 303 | 304 | A urna reiniciou logo após um voto: há 304 linhas "Voto confirmado para [Presidente]", mas só 303 linhas "O voto do eleitor foi computado". |
| `o03221pi1153300030216` | 258 | 259 | Idem (259 confirmados). |
| `o03221ba3471100210178` | 233 | 234 | Idem (234 confirmados). |

Nos três primeiros casos, a contagem do log fica **maior** que o BU porque `processa.py` soma todos os logs
do pacote. Isso é proposital: a regra é extrair sem interpretar, e assim a anomalia do pacote aparece.
Os votos excedentes desses três casos são todos anteriores às 17h de Brasília. Somados aos casos com log a menos, o saldo é de 213 votos a mais no log do que no BU.

## Arquivos fora do padrão nos zips

Dezenove UFs trazem arquivos `.id` fora do padrão de nomes de seção (lista em `saida/extras/`). Abrimos
`se0-sdjkADYayq-9IGAwt7Kc4ewW+hrQ09v-buq4S84=.id` (AP): ele tem 47 bytes e o conteúdo é o próprio nome do
arquivo. Não há dado de seção. Fora esses, os extras são apenas `leiame.pdf`.
