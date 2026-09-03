# Exact examples — last 3 weeks delivered

Window: `delivery_date` last 3 weeks. Complete distance fields only.

Download CSV: `delivered_3w_bucket_examples.csv`

## misshipping

Inducted in sibling parent WH state (different WH under same parent_suid)

| ops | tracking | supplier | own→actual hub | dest | asg→cust | act→cust | asg→act |
|-----|----------|----------|----------------|------|----------|----------|---------|
| 80205131550 | `538122031118` | CHANGSHA BATHROOM BUTLER DEZIGN INC OR 97007 | OH / WEST PORTLAND → **Sanford (FL)** | WI | 2070 | 1265 | 3037 |
| 80226820130 | `538130329147` | ROGER HOUSE LLC OR 97214-4656 | OR / WEST PORTLAND → **Sanford (FL)** | CA | 609 | 2906 | 3037 |
| 80203787590 | `538120794222` | long yan shi shang lao wu mao yi you xian gong si_1 OR 97214 | OR / WEST PORTLAND → **Sanford (FL)** | UT | 790 | 2332 | 3037 |
| 80203578680 | `538120794196` | CHANGSHA BATHROOM BUTLER DEZIGN INC OR 97007 | OH / WEST PORTLAND → **Sanford (FL)** | OR | 7 | 3040 | 3037 |
| 80227458080 | `538131279719` | ROGER HOUSE LLC OR 97214-4656 | OR / WEST PORTLAND → **Sanford (FL)** | CA | 978 | 2493 | 3037 |

## ghost

Far from assigned WH (>=200mi) and NOT closer to customer than assigned

| ops | tracking | supplier | own→actual hub | dest | asg→cust | act→cust | asg→act |
|-----|----------|----------|----------------|------|----------|----------|---------|
| 80214178950 | `383309956773` | Garage & Sliding Doors Express LLC FL 33020 | FL / FORT LAUDERDALE → **Fremont (CA)** | MI | 1387 | 2352 | 3066 |
| 80223445330 | `383369996500` | Garage & Sliding Doors Express LLC FL 33020 | FL / FORT LAUDERDALE → **Fremont (CA)** | MO | 1204 | 2065 | 3066 |
| 80207418230 | `383236710869` | World Source Partners WA  98424 | WA / TACOMA → **North Haven (CT)** | WA | 142 | 2985 | 2949 |
| 80215593710 | `538125844510` | Shenzhen Yunyao Technology Co., LTD CA 91731 | CA / ARCADIA → **Seekonk (MA)** | TX | 1450 | 1711 | 2947 |
| 80210678920 | `538124274998` | Porcelanosa NJ 07446 | NJ / SAN JOSE → **Spring Valley (NY)** | CA | 9 | 2954 | 2946 |

## other_closer

Wrong hub but actual induction closer to customer than assigned

| ops | tracking | supplier | own→actual hub | dest | asg→cust | act→cust | asg→act |
|-----|----------|----------|----------------|------|----------|----------|---------|
| 80207106310 | `875984450003` | Hawkins New York. | NY / ALBANY → **San Leandro (CA)** | CA | 2945 | 0 | 2945 |
| 80207106320 | `875984450003` | Hawkins New York. | NY / ALBANY → **San Leandro (CA)** | CA | 2945 | 0 | 2945 |
| 80204277160 | `538120796762` | WHALL GLOBAL BUSINESS LIMITED CA 94538 | CA / FREMONT → **East Brunswick (NJ)** | NY | 2939 | 41 | 2920 |
| 80222056830 | `538128614245` | LINKSTYLE.LIFE CA 94538 | CA / FREMONT → **Woodbridge (NJ)** | NY | 2932 | 37 | 2920 |
| 80220869460 | `538127784524` | Shenzhen Litian Technology Co., Ltd CA  95304 | CA / ROBBINSVILLE → **Tracy (CA)** | CA | 2962 | 70 | 2894 |
