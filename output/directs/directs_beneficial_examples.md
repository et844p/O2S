# Beneficial directs — concrete examples

Same supplier, same dest region: **direct path vs their own local path**. Benefit = lower O2D actual.

## Summary table

| Example | Direct vol | Local vol | Direct O2D | Local O2D | Δ | Direct IFR | Local IFR | Direct hub |
|---------|------------|-----------|------------|-----------|---|------------|-----------|------------|
| Surge: Kingston → Southeast (2026-06-07) | 121 | 10 | 7.67 | 10.00 | **-2.33d** | 100% | 100% | Marietta |
| Surge: CA2 → Midwest (2026-05-24) | 195 | 24 | 6.14 | 6.88 | **-0.74d** | 73% | 62% | Chicago |
| Surge: Hangzhou Mengfeisi → Midwest (2026-05-24) | 180 | 15 | 6.86 | 8.60 | **-1.74d** | 99% | 73% | Toledo |
| Surge: California Umbrella → Northeast (2026-05-24) | 14 | 33 | 7.43 | 9.82 | **-2.39d** | 100% | 100% | Metuchen |
| Surge: MKAY GROUP → Midwest (2026-05-31) | 52 | 24 | 7.75 | 15.54 | **-7.79d** | 100% | 50% | Chicago |
| Surge: Grand Leisure → Midwest (2026-05-31) | 36 | 13 | 7.47 | 10.69 | **-3.22d** | 100% | 92% | Chicago |
| OF: California Umbrella → Northeast (May–Aug) | 281 | 799 | 10.73 | 13.46 | **-2.74d** | 99% | 92% | Metuchen |
| OF: California Umbrella → Midwest (May–Aug) | 320 | 994 | 11.88 | 13.01 | **-1.13d** | 99% | 95% | Chicago |
| OF: Modway → South Central (May–Aug) | 430 | 1440 | 4.99 | 5.43 | **-0.44d** | 75% | 60% | West Dallas Ncpc |
| OF: CA2 → Southeast (May–Aug) | 351 | 368 | 5.66 | 6.01 | **-0.35d** | 68% | 91% | Greensboro |

## Sample trackings (direct vs local)

### Surge: Kingston → Southeast (2026-06-07)

**direct**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `500738871940` | 660242930 | MS 38655 | CHINO LOCAL → Olive Branch | 4 | 1 | 1 | 80 |
| `381919188440` | 661194952 | NC 28409 | CHINO LOCAL → Greensboro | 7 | 1 | 1 | 226 |
| `500738882204` | 661128308 | GA 30606 | CHINO LOCAL → Marietta | 8 | 1 | 1 | 80 |
| `381893437363` | 660514804 | SC 29466 | CHINO LOCAL → Charlotte | 11 | 1 | 0 | 217 |

**local**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `381982459569` | 661506781 | MS 39666 | CHINO LOCAL → Industry | 6 | 1 | 1 | 1882 |
| `500738887950` | 661481651 | KY 42071 | CHINO LOCAL → Industry | 7 | 1 | 1 | 1929 |
| `500738887630` | 661523831 | SC 29210 | CHINO LOCAL → Industry | 8 | 1 | 0 | 2367 |
| `500738887802` | 661469036 | GA 30114 | CHINO LOCAL → Industry | 33 | 1 | 0 | 2174 |

### Surge: CA2 → Midwest (2026-05-24)

**direct**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `872275969506` | 658683148 | IL 60046 | INDUSTRY → Chicago | 2 | 1 | 1 | 60 |
| `872213048387` | 658272884 | MN 55347 | INDUSTRY → St. Paul | 5 | 0 | 1 | 38 |
| `872155734122` | 657386881 | IL 60120 | INDUSTRY → East Carol Stream | 7 | 1 | 1 | 17 |
| `872181618955` | 657915057 | OH 43023 | INDUSTRY → East Columbus | 10 | 0 | 0 | 24 |

**local**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `872185119346` | 657677908 | NE 68508 | INDUSTRY → Kansas City | 4 | 1 | 1 | nan |
| `872181071310` | 657673090 | IA 51401 | INDUSTRY → North Kansas City Ncpc | 6 | 1 | 1 | nan |
| `872214995361` | 658314369 | IA 50266 | INDUSTRY → North Kansas City Ncpc | 8 | 0 | 0 | 180 |
| `872168204711` | 657506826 | IA 50849 | INDUSTRY → North Kansas City Ncpc | 10 | 1 | 0 | nan |

### Surge: Hangzhou Mengfeisi → Midwest (2026-05-24)

**direct**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `872264219067` | 658316470 | IA 52404 | RIALTO LOCAL → Cedar Rapids | 4 | 1 | 1 | 0 |
| `872232657236` | 658511050 | IN 46385 | RIALTO LOCAL → Chicago | 6 | 1 | 1 | 59 |
| `872198666562` | 658192268 | OH 44256 | RIALTO LOCAL → Columbus | 7 | 1 | 1 | 126 |
| `872570723939` | 658182414 | MO 63376 | RIALTO LOCAL → North St.Louis | 15 | 0 | 0 | 0 |

**local**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `872135808424` | 657268739 | MO 63876 | RIALTO LOCAL → Olive Branch | 5 | 1 | 1 | 117 |
| `872264207902` | 657842695 | IA 52534 | RIALTO LOCAL → Cedar Rapids | 6 | 1 | 1 | nan |
| `872570712107` | 658291252 | NE 68521 | RIALTO LOCAL → North Kansas City Ncpc | 7 | 1 | 1 | 205 |
| `872570708137` | 657862176 | IA 51465 | RIALTO LOCAL → Fort Dodge | 15 | 0 | 0 | nan |

### Surge: California Umbrella → Northeast (2026-05-24)

**direct**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `871947571530` | 656383858 | PA 18064 | RIALTO LOCAL → Breinigsville | 4 | 1 | 1 | 25 |
| `871950047664` | 656193052 | NY 11362 | RIALTO LOCAL → Metuchen | 5 | 1 | 1 | 49 |
| `872055214363` | 656475811 | PA 15071 | RIALTO LOCAL → West Columbus | 9 | 1 | 1 | 201 |
| `871954506711` | 654945902 | NY 10012 | RIALTO LOCAL → New York | 15 | 1 | 0 | 4 |

**local**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `871593558391` | 654399791 | PA 18966 | RIALTO LOCAL → Rialto | 6 | 1 | 1 | 2682 |
| `871279813602` | 652133181 | PA 18013 | RIALTO LOCAL → Rialto | 8 | 1 | 1 | 2684 |
| `871286828813` | 652078358 | NY 14618 | RIALTO LOCAL → Rialto | 11 | 1 | 1 | 2572 |
| `871406168621` | 651986702 | NY 10594 | RIALTO LOCAL → Rialto | 14 | 1 | 1 | 2771 |

### Surge: MKAY GROUP → Midwest (2026-05-31)

**direct**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `381663444150` | 658954018 | OH 43543 | INDUSTRY → Toledo | 6 | 1 | 1 | 58 |
| `381704243895` | 659124238 | IL 60514 | INDUSTRY → Chicago | 7 | 1 | 1 | 11 |
| `381742932074` | 659653696 | WI 53589 | INDUSTRY → Chicago | 8 | 1 | 1 | 135 |
| `381696694222` | 659133835 | MN 55987 | INDUSTRY → La Crosse | 10 | 1 | 1 | 29 |

**local**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `381664090751` | 658884603 | IA 50023 | INDUSTRY → Kansas City | 7 | 1 | 1 | 198 |
| `381742934490` | 659735873 | MO 65470 | INDUSTRY → Rolla | 7 | 1 | 1 | nan |
| `381745391010` | 659450547 | IL 60517 | INDUSTRY → Arcadia | 21 | 0 | 0 | 1985 |
| `381797438535` | 660164821 | NE 68130 | INDUSTRY → Industry | 55 | 0 | 0 | 1518 |

### Surge: Grand Leisure → Midwest (2026-05-31)

**direct**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `526519131063` | 659538096 | IL 60015 | WEST RIALTO → Romeoville Ncpc | 5 | 1 | 1 | 46 |
| `526513510881` | 658097130 | WI 53703 | WEST RIALTO → Mccook | 7 | 1 | 1 | 139 |
| `526515960342` | 658808516 | MN 56401 | WEST RIALTO → New Brighton Ncpc | 8 | 1 | 0 | 127 |
| `526511235288` | 657907027 | IL 60565 | WEST RIALTO → Chicago | 9 | 1 | 1 | 23 |

**local**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `526521224421` | 660043382 | NE 68133 | WEST RIALTO → North Kansas City Ncpc | 6 | 1 | 1 | nan |
| `526524726666` | 660323400 | IL 60180 | WEST RIALTO → Romeoville Rsf | 7 | 1 | 1 | 64 |
| `526516797796` | 658749327 | OH 43525 | WEST RIALTO → Toledo | 9 | 1 | 0 | 11 |
| `531274415357` | 657890289 | MN 55811 | WEST RIALTO → South Rialto - Ncpc | 44 | 0 | 0 | 2034 |

### OF: California Umbrella → Northeast (May–Aug)

**direct**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `872789837210` | 661023022 | NY 10014 | RIALTO LOCAL → Metuchen | 4 | 1 | 1 | 37 |
| `872912803044` | 661238353 | NY 11795 | RIALTO LOCAL → Metuchen | 8 | 1 | 1 | 80 |
| `872043800418` | 656173208 | NY 11563 | RIALTO LOCAL → Woodbridge | 11 | 1 | 1 | 52 |
| `872940363517` | 656168531 | NY 10804 | RIALTO LOCAL → Metuchen | 31 | 1 | 0 | 56 |

**local**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `870447038939` | 648008318 | PA 15232 | RIALTO LOCAL → Rialto | 3 | 1 | 1 | 2396 |
| `873170374176` | 662285003 | NY 10543 | RIALTO LOCAL → Rialto | 8 | 1 | 1 | 2766 |
| `871764764704` | 653638132 | PA 17837 | RIALTO LOCAL → Rialto | 15 | 1 | 1 | 2582 |
| `874803883860` | 660780703 | NY 11792 | RIALTO LOCAL → Rialto | 52 | 0 | 0 | 2821 |

### OF: California Umbrella → Midwest (May–Aug)

**direct**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `872145411328` | 657268014 | MN 55391 | RIALTO LOCAL → Maple Grove | 5 | 1 | 1 | 20 |
| `872362895205` | 658615753 | MI 48304 | RIALTO LOCAL → Toledo | 9 | 1 | 1 | 95 |
| `872674770233` | 658800940 | IL 60614 | RIALTO LOCAL → Chicago | 13 | 1 | 0 | 16 |
| `872960997190` | 656708087 | IN 46062 | RIALTO LOCAL → Chicago | 29 | 1 | 0 | 177 |

**local**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `873208682434` | 662716734 | ND 58201 | RIALTO LOCAL → nan | 2 | 1 | 1 | nan |
| `871274993611` | 652300604 | MN 55315 | RIALTO LOCAL → Rialto | 8 | 1 | 1 | 1849 |
| `871142296738` | 650505249 | WI 53955 | RIALTO LOCAL → Rialto | 12 | 1 | 0 | 1962 |
| `874600012151` | 660252121 | MI 48108 | RIALTO LOCAL → Rialto | 50 | 0 | 0 | 2201 |

### OF: Modway → South Central (May–Aug)

**direct**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `872028585577` | 656802556 | OK 73012 | WEST RIALTO → West Dallas Ncpc | 3 | 1 | 1 | 223 |
| `872681902627` | 660384787 | TX 78373 | WEST RIALTO → Houston | 4 | 1 | 1 | 265 |
| `872895389337` | 661382687 | TX 77055 | WEST RIALTO → Houston | 5 | 1 | 1 | 20 |
| `872371912180` | 659005122 | AR 72116 | WEST RIALTO → Memphis | 9 | 0 | 0 | 136 |

**local**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `871525196766` | 654154112 | TX 78723 | WEST RIALTO → South Rialto - Ncpc | 3 | 1 | 1 | 1331 |
| `875265429941` | 671914596 | OK 74745 | WEST RIALTO → South Rialto - Ncpc | 5 | 1 | 1 | 1524 |
| `874546095341` | 668447868 | TX 78660 | WEST RIALTO → South Rialto - Ncpc | 6 | 1 | 1 | 1342 |
| `873859107752` | 665572674 | TX 77459 | WEST RIALTO → South Rialto - Ncpc | 13 | 0 | 0 | 1494 |

### OF: CA2 → Southeast (May–Aug)

**direct**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `872683485909` | 660376859 | NC 28202 | INDUSTRY → Spartanburg | 2 | 1 | 1 | 74 |
| `872630461140` | 660164912 | NC 27519 | INDUSTRY → Greensboro | 4 | 0 | 1 | 91 |
| `871887021051` | 655882850 | NC 28025 | INDUSTRY → North Charlotte Rsf | 7 | 1 | 1 | 16 |
| `873059942813` | 662136302 | TN 38002 | INDUSTRY → East Chattanooga | 12 | 0 | 0 | 332 |

**local**

| Tracking | PO | Dest | Assigned → Actual | O2D act | IFR | Del | Mi to cust |
|----------|----|------|-------------------|---------|-----|-----|------------|
| `871735667510` | 655173697 | AL 36109 | INDUSTRY → nan | 2 | 1 | 1 | nan |
| `873356778520` | 663543867 | SC 29407 | INDUSTRY → Arcadia | 5 | 1 | 1 | 2479 |
| `871290900735` | 652753860 | TN 37082 | INDUSTRY → Arcadia | 7 | 1 | 1 | 1964 |
| `873491027330` | 662973625 | SC 29910 | INDUSTRY → Arcadia | 12 | 0 | 0 | 2427 |

## Files

- `directs_beneficial_examples.xlsx` — summary + trackings + fuller supplier lists
- `directs_beneficial_surge_supplier_examples.csv` — 122 surge within-supplier wins
- `directs_beneficial_outdoor_supplier_examples.csv` — 47 Outdoor Furniture wins
