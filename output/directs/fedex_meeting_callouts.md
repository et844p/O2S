# FedEx meeting callouts — last 10 weeks (PDD), DS only

Classification: candidate = wrong hub + cust≥400 + hub≥200; then misshipping → ghost → jumbo → direct.

## Headline: Safavieh CA 92518 (ghost) — check warehouse address

- Registered: `20800 Krameria Aveune, Riverside, CA 92518` (note typo Aveune)
- Assigned hub in data: mostly **Rialto Local (CA)**; some rows show North Indianapolis
- **58.4% of vol inducts at Fairfield Annex (CA)** (~449 mi from Rialto) — 11,022 of 18,889 ops
- Of Fairfield volume, 5,902 meet candidate distance rules → classified **ghost_warehouse**
- Avg direct_gain on Fairfield candidates is near 0 / negative — not a customer-gain direct
- Ask FedEx / supplier: is there an undeclared NorCal ship point near Fairfield, or is the Riverside address wrong/outdated?

### Safavieh Fairfield Annex sample trackings
- `875325974145` PO `672076222` | assigned=RIALTO LOCAL → actual=Fairfield Annex (CA) | dest=SC 29669 | hub_mi=448.70 gain=
- `875327114162` PO `671976239` | assigned=RIALTO LOCAL → actual=Fairfield Annex (CA) | dest=IN 47201 | hub_mi=448.70 gain=-0.10
- `875264689979` PO `671642279` | assigned=RIALTO LOCAL → actual=Fairfield Annex (CA) | dest=nan 02127 | hub_mi=448.70 gain=
- `875267078080` PO `671736299` | assigned=RIALTO LOCAL → actual=Fairfield Annex (CA) | dest=nan 02747 | hub_mi=448.70 gain=
- `875442845174` PO `672472348` | assigned=RIALTO LOCAL → actual=Fairfield Annex (CA) | dest=CA 94070 | hub_mi=448.70 gain=0.84
- `875494646676` PO `672641122` | assigned=RIALTO LOCAL → actual=Fairfield Annex (CA) | dest=CA 91344 | hub_mi=448.70 gain=-3.65
- `875491862760` PO `672624597` | assigned=RIALTO LOCAL → actual=Fairfield Annex (CA) | dest=CA 91344 | hub_mi=448.70 gain=-3.65
- `875475391068` PO `672475690` | assigned=RIALTO LOCAL → actual=Fairfield Annex (CA) | dest=CO 80016 | hub_mi=448.70 gain=-0.24

## Top 5 — Ghost warehouse
_Persistent far hub ≥10% vol, most weeks, not a sibling WH state_

### 1. Safavieh CA 92518 (SUID 59119)
- Addr: 20800 Krameria Aveune, Riverside 92518 (CA)
- Assigned: NORTH  INDIANAPOLIS (IN) | top actual hub: Fairfield Annex (CA) 58% of total
- Bucket vol: 5,902 (31.2% of supplier) | IFR=92.0% | del_rel=79.9% | avg_gain=0.07
- Sample hubs in bucket: Fairfield Annex (CA)
- Sample trackings to validate:
  - `875267059534` | RIALTO LOCAL→Fairfield Annex (CA) | dest=NY | hub_mi=448.70 | cust_asg=2608.00 cust_act= | gain=
  - `875267370022` | RIALTO LOCAL→Fairfield Annex (CA) | dest=FL | hub_mi=448.70 | cust_asg=2610.20 cust_act=3057.60 | gain=-0.17
  - `875272656508` | RIALTO LOCAL→Fairfield Annex (CA) | dest=GA | hub_mi=448.70 | cust_asg=2340.30 cust_act=2685.50 | gain=-0.15
  - `875325596528` | RIALTO LOCAL→Fairfield Annex (CA) | dest=FL | hub_mi=448.70 | cust_asg=2636.80 cust_act=3083.10 | gain=-0.17
  - `875265097186` | RIALTO LOCAL→Fairfield Annex (CA) | dest=NY | hub_mi=448.70 | cust_asg=2772.30 cust_act= | gain=

### 2. CIAO JING INC CA 92879  (SUID 293214)
- Addr: 2565 Sampson Ave , Corona 92879 (CA)
- Assigned: WEST RIALTO (CA) | top actual hub: Fairfield Annex (CA) 67% of total
- Bucket vol: 2,529 (45.9% of supplier) | IFR=82.2% | del_rel=77.8% | avg_gain=-0.06
- Sample hubs in bucket: Fairfield Annex (CA)
- Sample trackings to validate:
  - `531304238966` | WEST RIALTO→Fairfield Annex (CA) | dest=IL | hub_mi=448.70 | cust_asg=1985.90 cust_act=2095.70 | gain=-0.06
  - `531300677307` | MISSOULA→Fairfield Annex (CA) | dest=KS | hub_mi=937.40 | cust_asg=1401.30 cust_act=1777.90 | gain=-0.27
  - `531300677318` | MISSOULA→Fairfield Annex (CA) | dest=KS | hub_mi=937.40 | cust_asg=1401.30 cust_act=1777.90 | gain=-0.27
  - `531300677318` | MISSOULA→Fairfield Annex (CA) | dest=KS | hub_mi=937.40 | cust_asg=1401.30 cust_act=1777.90 | gain=-0.27
  - `531300677281` | MISSOULA→Fairfield Annex (CA) | dest=KS | hub_mi=937.40 | cust_asg=1401.30 cust_act=1777.90 | gain=-0.27

### 3. Compamia FL 33147 (SUID 155962)
- Addr: 7000 N W 32 AVE, Miami 33147 (FL)
- Assigned: MEDLEY (FL) | top actual hub: Williamsburg Ncpc (FL) 45% of total
- Bucket vol: 2,421 (30.6% of supplier) | IFR=92.4% | del_rel=89.2% | avg_gain=0.16
- Sample hubs in bucket: Williamsburg Ncpc (FL)
- Sample trackings to validate:
  - `873432988430` | MEDLEY→Williamsburg Ncpc (FL) | dest=NY | hub_mi=234.00 | cust_asg=1385.30 cust_act= | gain=
  - `875019592264` | MEDLEY→Williamsburg Ncpc (FL) | dest=CA | hub_mi=234.00 | cust_asg=3107.40 cust_act=2895.70 | gain=0.07
  - `874987432533` | MEDLEY→Williamsburg Ncpc (FL) | dest=WA | hub_mi=234.00 | cust_asg=3327.90 cust_act=3116.20 | gain=0.06
  - `874993923630` | MEDLEY→Williamsburg Ncpc (FL) | dest=WA | hub_mi=234.00 | cust_asg=3391.40 cust_act=3179.70 | gain=0.06
  - `874995973010` | MEDLEY→Williamsburg Ncpc (FL) | dest=CA | hub_mi=234.00 | cust_asg=2903.30 cust_act= | gain=

### 4. Edecor Center Inc._1 NJ 08110 (SUID 253370)
- Addr: 1050 Thomas Busch Memorial Highway, Pennsauken 8110 (NJ)
- Assigned: CAMDEN (NJ) | top actual hub: Fairless Hills (PA) 44% of total
- Bucket vol: 2,232 (35.2% of supplier) | IFR=73.5% | del_rel=84.0% | avg_gain=0.61
- Sample hubs in bucket: Diamond Bar Rsf (CA); South Dallas Rsf (TX)
- Sample trackings to validate:
  - `531308011271` | CAMDEN→Diamond Bar Rsf (CA) | dest=CA | hub_mi=2704.90 | cust_asg=2727.30 cust_act=31.20 | gain=0.99
  - `531308011054` | CAMDEN→Diamond Bar Rsf (CA) | dest=AZ | hub_mi=2704.90 | cust_asg=2406.80 cust_act=347.70 | gain=0.86
  - `531307907553` | CAMDEN→South Dallas Rsf (TX) | dest=MN | hub_mi=1478.50 | cust_asg=1224.00 cust_act=986.20 | gain=0.19
  - `531308349994` | CAMDEN→South Dallas Rsf (TX) | dest=MN | hub_mi=1478.50 | cust_asg=1172.90 cust_act=953.20 | gain=0.19
  - `531308387193` | CAMDEN→South Dallas Rsf (TX) | dest=WI | hub_mi=1478.50 | cust_asg=1059.80 cust_act=975.40 | gain=0.08

### 5. WPLA4 (SUID 211658)
- Addr: 13083 Slover Ave, Fontana 92337 (CA)
- Assigned: WEST RIALTO (CA) | top actual hub: Fairfield Annex (CA) 66% of total
- Bucket vol: 1,566 (38.1% of supplier) | IFR=85.3% | del_rel=75.9% | avg_gain=0.03
- Sample hubs in bucket: Fairfield Annex (CA)
- Sample trackings to validate:
  - `531308234624` | WEST RIALTO→Fairfield Annex (CA) | dest=TX | hub_mi=448.70 | cust_asg=1509.80 cust_act=1956.70 | gain=-0.30
  - `531305750614` | WEST RIALTO→Fairfield Annex (CA) | dest=VA | hub_mi=448.70 | cust_asg=2573.70 cust_act=2819.60 | gain=-0.10
  - `531305922090` | WEST RIALTO→Fairfield Annex (CA) | dest=AL | hub_mi=448.70 | cust_asg=1948.60 cust_act= | gain=
  - `531306055017` | WEST RIALTO→Fairfield Annex (CA) | dest=NC | hub_mi=448.70 | cust_asg=2551.90 cust_act=2896.80 | gain=-0.14
  - `531306144550` | WEST RIALTO→Fairfield Annex (CA) | dest=NY | hub_mi=448.70 | cust_asg=2810.60 cust_act=2920.40 | gain=-0.04

## Top 5 — Misshipping
_Inducting in a state where parent already has another WH_

### 1. NW Investment Inc TX 75041 (SUID 302333)
- Addr: 3422 W Kingsley Rd, Garland 75041 (TX)
- Assigned: MESQUITE (TX) | top actual hub: South Dallas Rsf (TX) 42% of total
- Bucket vol: 3,485 (35.5% of supplier) | IFR=93.4% | del_rel=90.3% | avg_gain=0.45
- Sample hubs in bucket: Stockton Rsf (CA); Diamond Bar Rsf (CA); King Of Prussia (PA); Fresno (CA); Sacramento (CA)
- Sample trackings to validate:
  - `531303244450` | MESQUITE→Diamond Bar Rsf (CA) | dest=WA | hub_mi=1424.10 | cust_asg=2146.30 cust_act=1020.00 | gain=0.52
  - `531307587538` | MESQUITE→Fairless Hills (PA) | dest=PA | hub_mi=1479.60 | cust_asg=1441.20 cust_act=52.70 | gain=0.96
  - `531307149948` | MESQUITE→Fairless Hills (PA) | dest=IN | hub_mi=1479.60 | cust_asg=1039.50 cust_act=645.90 | gain=0.38
  - `531307858805` | MESQUITE→Fairless Hills (PA) | dest=OH | hub_mi=1479.60 | cust_asg=1049.80 cust_act=479.90 | gain=0.54
  - `531307149948` | MESQUITE→Fairless Hills (PA) | dest=IN | hub_mi=1479.60 | cust_asg=1039.50 cust_act=645.90 | gain=0.38

### 2. Baishi NJ 08810 Bedshe (SUID 292469)
- Addr: 11 Corn Rd , Dayton  8810 (NJ)
- Assigned: PRINCETON (NJ) | top actual hub: East Brunswick (NJ) 57% of total
- Bucket vol: 2,385 (16.1% of supplier) | IFR=97.4% | del_rel=25.7% | avg_gain=-1.35
- Sample hubs in bucket: Sacramento (CA); Arcadia (CA); South Rialto - Ncpc (CA); Lubbock (TX); Tyler (TX)
- Sample trackings to validate:
  - `531307868427` | PRINCETON→Chino (CA) | dest=GA | hub_mi=2729.90 | cust_asg=821.70 cust_act=2319.40 | gain=-1.82
  - `531307868427` | PRINCETON→Chino (CA) | dest=GA | hub_mi=2729.90 | cust_asg=821.70 cust_act=2319.40 | gain=-1.82
  - `531308106210` | PRINCETON→Chino (CA) | dest=FL | hub_mi=2729.90 | cust_asg=1244.90 cust_act=2673.80 | gain=-1.15
  - `531306584500` | PRINCETON→Chino (CA) | dest=FL | hub_mi=2729.90 | cust_asg=1330.30 cust_act=2776.10 | gain=-1.09
  - `531306732346` | PRINCETON→Chino (CA) | dest=MS | hub_mi=2729.90 | cust_asg=1218.90 cust_act=1926.60 | gain=-0.58

### 3. Unique Loom SC29707 (SUID 34657)
- Addr: 793 Fort Mill Highway, Fort Mill 29707 (SC)
- Assigned: FORT MILL (SC) | top actual hub: Fort Mill (SC) 75% of total
- Bucket vol: 1,869 (4.4% of supplier) | IFR=86.4% | del_rel=89.7% | avg_gain=0.73
- Sample hubs in bucket: Rialto Local (CA); Burbank (CA); San Jose (CA); Santa Maria (CA); Fresno (CA)
- Sample trackings to validate:
  - `382968453909` | FORT MILL→Fresno (CA) | dest=CA | hub_mi=2543.50 | cust_asg=2713.20 cust_act=180.60 | gain=0.93
  - `382967292054` | FORT MILL→Fresno (CA) | dest=CA | hub_mi=2543.50 | cust_asg=2713.20 cust_act=180.60 | gain=0.93
  - `382969233183` | FORT MILL→Fresno (CA) | dest=OR | hub_mi=2543.50 | cust_asg=2913.30 cust_act=625.40 | gain=0.79
  - `382969233183` | FORT MILL→Fresno (CA) | dest=OR | hub_mi=2543.50 | cust_asg=2913.30 cust_act=625.40 | gain=0.79
  - `382993288975` | FORT MILL→Fresno (CA) | dest=NV | hub_mi=2543.50 | cust_asg=2215.70 cust_act=395.80 | gain=0.82

### 4. Surya GA 30184 (1 Surya Dr) (SUID 22696)
- Addr: 1 Surya Drive, White 30184 (GA)
- Assigned: MARIETTA LOCAL (GA) | top actual hub: Marietta (GA) 43% of total
- Bucket vol: 1,596 (1.4% of supplier) | IFR=94.8% | del_rel=82.0% | avg_gain=0.96
- Sample hubs in bucket: Chino Local (CA); Hayward (CA); Arcadia (CA); Oceanside (CA); Bishop (CA)
- Sample trackings to validate:
  - `872553039903` | MARIETTA LOCAL→Tracy (CA) | dest=CA | hub_mi=2429.90 | cust_asg=2523.60 cust_act=105.30 | gain=0.96
  - `872636102390` | MARIETTA LOCAL→Tracy (CA) | dest=NV | hub_mi=2429.90 | cust_asg=2359.30 cust_act=203.30 | gain=0.91
  - `872315184637` | MARIETTA LOCAL→Chino (CA) | dest=CA | hub_mi=2151.20 | cust_asg=2226.60 cust_act=86.00 | gain=0.96
  - `872628031087` | MARIETTA LOCAL→Rialto (CA) | dest=CA | hub_mi=2139.50 | cust_asg=2164.00 cust_act=37.60 | gain=0.98
  - `872628031087` | MARIETTA LOCAL→Rialto (CA) | dest=CA | hub_mi=2139.50 | cust_asg=2164.00 cust_act=37.60 | gain=0.98

### 5. York Wallcoverings PA 17408 (SUID 350373)
- Addr: 2075 Loucks Road, York 17408 (PA)
- Assigned: HARRISBURG LOCAL (PA) | top actual hub: Harrisburg Local (PA) 33% of total
- Bucket vol: 1,575 (10.1% of supplier) | IFR=91.4% | del_rel=91.8% | avg_gain=0.25
- Sample hubs in bucket: Mansfield (OH); Toledo (OH); Groveport  (OH); Cincinnati (OH); Columbus (OH)
- Sample trackings to validate:
  - `521481231090` | HARRISBURG LOCAL→Columbus (OH) | dest=NV | hub_mi=378.50 | cust_asg=2410.30 cust_act=2036.10 | gain=0.16
  - `534866672209` | HARRISBURG LOCAL→Columbus (OH) | dest=CO | hub_mi=378.50 | cust_asg=1930.90 cust_act=1555.00 | gain=0.19
  - `534866679773` | HARRISBURG LOCAL→Columbus (OH) | dest=SC | hub_mi=378.50 | cust_asg=554.40 cust_act=614.40 | gain=-0.11
  - `534866672297` | HARRISBURG LOCAL→Columbus (OH) | dest=TX | hub_mi=378.50 | cust_asg=1498.80 cust_act=1177.40 | gain=0.21
  - `521481229413` | HARRISBURG LOCAL→Columbus (OH) | dest=CA | hub_mi=378.50 | cust_asg=2781.20 cust_act=2449.90 | gain=0.12

## Top 5 — Jumbo
_Candidate with direct_gain < 0.4_

### 1. NFusion GA 31407 (SUID 36423)
- Addr: 425 Jimmy Deloach Parkway, Savannah 31407 (GA)
- Assigned: SAVANNAH (GA) | top actual hub: West Savannah  Ncpc (GA) 41% of total
- Bucket vol: 2,704 (19.3% of supplier) | IFR=26.3% | del_rel=58.8% | avg_gain=-0.21
- Sample hubs in bucket: Braselton (GA); Fort Wayne (IN); Harrisburg (PA); Carlisle (PA); Goodyear Rsf (AZ)
- Sample trackings to validate:
  - `875217037101` | SAVANNAH→Ocala (FL) | dest=CA | hub_mi=234.70 | cust_asg=2452.20 cust_act= | gain=
  - `875346616451` | SAVANNAH→Ocala (FL) | dest=MS | hub_mi=234.70 | cust_asg=578.80 cust_act= | gain=
  - `875217114456` | SAVANNAH→Ocala (FL) | dest=CA | hub_mi=234.70 | cust_asg=2386.90 cust_act= | gain=
  - `875217027800` | SAVANNAH→Ocala (FL) | dest=CA | hub_mi=234.70 | cust_asg=2390.50 cust_act= | gain=
  - `875217440072` | SAVANNAH→Ocala (FL) | dest=CA | hub_mi=234.70 | cust_asg=2436.00 cust_act= | gain=

### 2. GigaCloud Trading, Inc. GA 31302 (SUID 302637)
- Addr: 3001 Jimmy Deloach Parkway, Bloomingdale 31302 (GA)
- Assigned: SAVANNAH (GA) | top actual hub: West Savannah  Ncpc (GA) 31% of total
- Bucket vol: 2,515 (22.2% of supplier) | IFR=39.5% | del_rel=77.5% | avg_gain=0.01
- Sample hubs in bucket: Lehigh Valley (PA); Aurora Local (CO); Albany (NY); Binghamton (NY); Billings (MT)
- Sample trackings to validate:
  - `875200393711` | SAVANNAH→Davenport (FL) | dest=CA | hub_mi=315.80 | cust_asg=2423.50 cust_act= | gain=
  - `875350619865` | SAVANNAH→Davenport (FL) | dest=CO | hub_mi=315.80 | cust_asg=1651.40 cust_act= | gain=
  - `875397561100` | SAVANNAH→South Atlanta Ncpc (GA) | dest=TX | hub_mi=239.00 | cust_asg=1097.70 cust_act=868.50 | gain=0.21
  - `875397929440` | SAVANNAH→South Atlanta Ncpc (GA) | dest=VA | hub_mi=239.00 | cust_asg=476.40 cust_act=552.30 | gain=-0.16
  - `875402987618` | SAVANNAH→Davenport (FL) | dest=NY | hub_mi=315.80 | cust_asg=859.30 cust_act=1164.80 | gain=-0.36

### 3.  美南SAV自营仓 (SUID 291275)
- Addr: 150 Knowlton Way Savannah, Savannah 31407 (GA)
- Assigned: HAGERSTOWN (MD) | top actual hub: West Savannah  Ncpc (GA) 39% of total
- Bucket vol: 1,035 (16.4% of supplier) | IFR=70.9% | del_rel=47.4% | avg_gain=-0.11
- Sample hubs in bucket: Portland (OR); Leesburg (VA); Olive Branch (MS); Van Buren Rsf (MI); Aurora (CO)
- Sample trackings to validate:
  - `531304945463` | WEST RIALTO→Davenport (FL) | dest=AL | hub_mi=2451.70 | cust_asg=1972.30 cust_act= | gain=
  - `531304957147` | SAVANNAH→Davenport (FL) | dest=CA | hub_mi=315.80 | cust_asg=2558.30 cust_act= | gain=
  - `531307093665` | PRINCETON→Richmond Hill Ncpc (GA) | dest=OK | hub_mi=784.80 | cust_asg=1357.90 cust_act= | gain=
  - `531307093665` | PRINCETON→Richmond Hill Ncpc (GA) | dest=OK | hub_mi=784.80 | cust_asg=1357.90 cust_act= | gain=
  - `531307176367` | PRINCETON→Richmond Hill Ncpc (GA) | dest=TX | hub_mi=784.80 | cust_asg=1516.70 cust_act=1035.30 | gain=0.32

### 4. Surya GA 30184 (1 Surya Dr) (SUID 22696)
- Addr: 1 Surya Drive, White 30184 (GA)
- Assigned: MARIETTA LOCAL (GA) | top actual hub: Marietta (GA) 43% of total
- Bucket vol: 1,011 (0.9% of supplier) | IFR=98.2% | del_rel=88.3% | avg_gain=0.10
- Sample hubs in bucket: Kansas City (MO); Toledo (OH); West Columbus (OH); Cedar Rapids (IA); North Kansas City Ncpc (MO)
- Sample trackings to validate:
  - `875486069320` | SAVANNAH→South Atlanta Ncpc (GA) | dest=TX | hub_mi=231.90 | cust_asg=1085.40 cust_act=864.90 | gain=0.20
  - `875430642382` | SAVANNAH→South Atlanta Ncpc (GA) | dest=LA | hub_mi=231.90 | cust_asg=733.10 cust_act=530.30 | gain=0.28
  - `875430697816` | SAVANNAH→South Atlanta Ncpc (GA) | dest=VA | hub_mi=231.90 | cust_asg=569.80 cust_act=600.20 | gain=-0.05
  - `875486134924` | SAVANNAH→South Atlanta Ncpc (GA) | dest=FL | hub_mi=231.90 | cust_asg=446.30 cust_act=565.40 | gain=-0.27
  - `875202595491` | SAVANNAH→Chattanooga (TN) | dest=CA | hub_mi=361.00 | cust_asg=2416.30 cust_act=2136.20 | gain=0.12

### 5. JLA Home GA 31407 - SV2 (SUID 35069)
- Addr: 550 Northport Pkwy, Port Wentworth 31407 (GA)
- Assigned: SAVANNAH (GA) | top actual hub: Savannah (GA) 83% of total
- Bucket vol: 842 (2.2% of supplier) | IFR=90.6% | del_rel=75.1% | avg_gain=-0.14
- Sample hubs in bucket: Murfreesboro (TN); Phoenix (AZ); Hagerstown (MD); North Pittsburgh (PA); Denver (CO)
- Sample trackings to validate:
  - `875237980586` | SAVANNAH→Chicago (IL) | dest=AL | hub_mi=959.70 | cust_asg=447.10 cust_act=716.40 | gain=-0.60
  - `875221313366` | HAGERSTOWN→Savannah (GA) | dest=NC | hub_mi=636.70 | cust_asg=425.80 cust_act=257.10 | gain=0.40
  - `874980898474` | HAGERSTOWN→Savannah (GA) | dest=OR | hub_mi=636.70 | cust_asg=2740.30 cust_act=2847.30 | gain=-0.04
  - `874905156749` | HAGERSTOWN→Savannah (GA) | dest=WA | hub_mi=636.70 | cust_asg=2754.60 cust_act=2859.90 | gain=-0.04
  - `875156737182` | HAGERSTOWN→Savannah (GA) | dest=TX | hub_mi=636.70 | cust_asg=1302.10 cust_act=1028.50 | gain=0.21

## Top 5 — Direct
_Candidate with direct_gain ≥ 0.4 (not misshipping/ghost)_

### 1. Surya GA 30184 (1 Surya Dr) (SUID 22696)
- Addr: 1 Surya Drive, White 30184 (GA)
- Assigned: MARIETTA LOCAL (GA) | top actual hub: Marietta (GA) 43% of total
- Bucket vol: 7,474 (6.6% of supplier) | IFR=99.1% | del_rel=88.6% | avg_gain=0.87
- Sample hubs in bucket: South Chesterfield (VA); South Key West (FL); South Houston (TX); North Portland (OR); Ogden (UT)
- Sample trackings to validate:
  - `872220017872` | MARIETTA LOCAL→Phoenix (AZ) | dest=AZ | hub_mi=1868.80 | cust_asg=1697.60 cust_act=169.30 | gain=0.90
  - `875292960327` | MARIETTA LOCAL→Northern Kentucky (KY) | dest=IL | hub_mi=438.80 | cust_asg=701.80 cust_act=320.30 | gain=0.54
  - `875202605198` | SAVANNAH→Chattanooga (TN) | dest=OH | hub_mi=361.00 | cust_asg=721.40 cust_act=415.00 | gain=0.42
  - `875274676395` | HAGERSTOWN→Marietta (GA) | dest=GA | hub_mi=658.00 | cust_asg=650.50 cust_act=11.60 | gain=0.98
  - `872627733461` | MARIETTA LOCAL→North Portland Rsf (OR) | dest=WA | hub_mi=2575.90 | cust_asg=2640.60 cust_act=170.30 | gain=0.94

### 2. Devion Furniture (SUID 237104)
- Addr: 4422 E Airport Drive, Ontario 91761 (CA)
- Assigned: CHINO LOCAL (CA) | top actual hub: Chino Hills Ncpc (CA) 68% of total
- Bucket vol: 6,010 (16.6% of supplier) | IFR=66.8% | del_rel=85.6% | avg_gain=0.95
- Sample hubs in bucket: Greensboro Local (NC); South Baltimore (MD); Olive Branch Local (MS); Hagerstown Local (MD); Kansas City Local (MO)
- Sample trackings to validate:
  - `526529622096` | CHINO LOCAL→Toledo (OH) | dest=MI | hub_mi=2208.70 | cust_asg=2261.60 cust_act=83.40 | gain=0.96
  - `526529622100` | CHINO LOCAL→Toledo (OH) | dest=MI | hub_mi=2208.70 | cust_asg=2261.60 cust_act=83.40 | gain=0.96
  - `526529622100` | CHINO LOCAL→Toledo (OH) | dest=MI | hub_mi=2208.70 | cust_asg=2261.60 cust_act=83.40 | gain=0.96
  - `526528830370` | CHINO LOCAL→Toledo (OH) | dest=MI | hub_mi=2208.70 | cust_asg=2268.60 cust_act=91.60 | gain=0.96
  - `526528830370` | CHINO LOCAL→Toledo (OH) | dest=MI | hub_mi=2208.70 | cust_asg=2268.60 cust_act=91.60 | gain=0.96

### 3. DesignArt Inc. NY (SUID 59806)
- Addr: 156 Lawrence Paquette Dr, Champlain 12919 (NY)
- Assigned: PLATTSBURGH (NY) | top actual hub: Plattsburgh (NY) 77% of total
- Bucket vol: 4,754 (13.5% of supplier) | IFR=88.4% | del_rel=90.9% | avg_gain=0.92
- Sample hubs in bucket: Houston (TX); South Chesterfield (VA); Gaithersburg (MD); Spartanburg (SC); Charlotte (NC)
- Sample trackings to validate:
  - `382875985745` | SOUTH RIALTO - NCPC→Plattsburgh (NY) | dest=WI | hub_mi=2812.70 | cust_asg=2060.60 cust_act=1178.80 | gain=0.43
  - `382701644227` | SOUTH RIALTO - NCPC→Plattsburgh (NY) | dest=IN | hub_mi=2812.70 | cust_asg=2108.80 cust_act=732.10 | gain=0.65
  - `382620770403` | ROMEOVILLE NCPC→Plattsburgh (NY) | dest=PA | hub_mi=911.60 | cust_asg=776.80 cust_act=388.50 | gain=0.50
  - `382409319882` | SAVANNAH→Plattsburgh (NY) | dest=NY | hub_mi=1104.20 | cust_asg=860.70 cust_act=348.80 | gain=0.59
  - `382252510120` | SAVANNAH→Plattsburgh (NY) | dest=PA | hub_mi=1104.20 | cust_asg=703.00 cust_act=404.40 | gain=0.42

### 4. Unique Loom SC29707 (SUID 34657)
- Addr: 793 Fort Mill Highway, Fort Mill 29707 (SC)
- Assigned: FORT MILL (SC) | top actual hub: Fort Mill (SC) 75% of total
- Bucket vol: 3,765 (8.9% of supplier) | IFR=59.6% | del_rel=66.5% | avg_gain=0.85
- Sample hubs in bucket: Sanford (FL); Oklahoma City (OK); Fort Mill (SC); Las Vegas (NV); Atlanta (GA)
- Sample trackings to validate:
  - `382924018220` | FRESNO→Fort Mill (SC) | dest=IL | hub_mi=2543.50 | cust_asg=2138.60 cust_act=795.80 | gain=0.63
  - `382924018220` | FRESNO→Fort Mill (SC) | dest=IL | hub_mi=2543.50 | cust_asg=2138.60 cust_act=795.80 | gain=0.63
  - `382824844009` | ROMEOVILLE NCPC→Fort Mill (SC) | dest=FL | hub_mi=793.50 | cust_asg=1237.20 cust_act=607.90 | gain=0.51
  - `381650819849` | FORT MILL→Greenwood (IN) | dest=IL | hub_mi=582.00 | cust_asg=780.50 cust_act=194.10 | gain=0.75
  - `381799233872` | FORT MILL→Mesquite (TX) | dest=OK | hub_mi=1028.80 | cust_asg=1097.20 cust_act=202.90 | gain=0.82

### 5. Wexford Home IL (SUID 44034)
- Addr: 7409 S QUNICY, WILLOWBROOK  60527 (IL)
- Assigned: BEDFORD PARK (IL) | top actual hub: Mccook (IL) 72% of total
- Bucket vol: 3,625 (9.5% of supplier) | IFR=88.7% | del_rel=85.4% | avg_gain=0.90
- Sample hubs in bucket: Chandler (AZ); East Syracuse (NY); Savannah (GA); Spokane (WA); Fort Smith (AR)
- Sample trackings to validate:
  - `531306534137` | SOUTH RIALTO - NCPC→Mccook (IL) | dest=MI | hub_mi=1957.90 | cust_asg=2235.10 cust_act=289.60 | gain=0.87
  - `531302295282` | BEDFORD PARK→Hagerstown (MD) | dest=MD | hub_mi=636.80 | cust_asg=735.40 cust_act=101.40 | gain=0.86
  - `531302295282` | BEDFORD PARK→Hagerstown (MD) | dest=MD | hub_mi=636.80 | cust_asg=735.40 cust_act=101.40 | gain=0.86
  - `531305430691` | SOUTH RIALTO - NCPC→Mccook (IL) | dest=VA | hub_mi=1957.90 | cust_asg=2623.60 cust_act=714.90 | gain=0.73
  - `531303710515` | OLIVE BRANCH→Mccook (IL) | dest=MI | hub_mi=550.80 | cust_asg=767.90 cust_act=312.40 | gain=0.59
