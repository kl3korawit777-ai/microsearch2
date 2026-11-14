# เทียบลักษณะกับ BacDive และ IUCN

สร้างจาก `python scripts/microsearch.py traits-diff` (ข้อมูลดิบ `data/generated/traits-fetched.json`)
รายงานนี้ **ไม่แก้ข้อมูลอัตโนมัติ** ค่าที่ API ให้ต้องผ่านการตรวจก่อนนำไปใส่ใน `data/organisms`

BacDive ใช้ type strain ของแต่ละชนิด ส่วน IUCN ใช้การประเมินล่าสุดระดับโลก

## สรุป

| หมวด | จำนวน |
| --- | --- |
| ตรงกัน | 35 |
| เราว่างแต่ API มี | 27 |
| ต่างกัน | 7 |
| API ไม่มี | 48 |
| ชนิดที่ไม่มีระเบียนจาก API เลย | 73 |

## ตรงกัน (35)

| ชนิด | ลักษณะ | ของเรา | API | ค่าดิบและแหล่ง |
| --- | --- | --- | --- | --- |
| `halobacterium-salinarum` | shape | rod | rod | [rod-shaped](https://bacdive.dsmz.de/strain/5912) |
| `methanobrevibacter-smithii` | oxy | ana | ana | [anaerobe](https://bacdive.dsmz.de/strain/6963) |
| `pyrococcus-furiosus` | oxy | ana | ana | [anaerobe](https://bacdive.dsmz.de/strain/16854) |
| `nitrosopumilus-maritimus` | shape | rod | rod | [rod-shaped](https://bacdive.dsmz.de/strain/141102) |
| `nitrosopumilus-maritimus` | oxy | aer | aer | [aerobe](https://bacdive.dsmz.de/strain/141102) |
| `methanosarcina-barkeri` | oxy | ana | ana | [anaerobe](https://bacdive.dsmz.de/strain/7087) |
| `methanocaldococcus-jannaschii` | oxy | ana | ana | [anaerobe](https://bacdive.dsmz.de/strain/6981) |
| `escherichia-coli` | shape | rod | rod | [rod-shaped](https://bacdive.dsmz.de/strain/4907) |
| `escherichia-coli` | gram | neg | neg | [negative](https://bacdive.dsmz.de/strain/4907) |
| `escherichia-coli` | oxy | fac | fac | [facultative anaerobe](https://bacdive.dsmz.de/strain/4907) |
| `rhizobium-leguminosarum` | shape | rod | rod | [rod-shaped](https://bacdive.dsmz.de/strain/138443) |
| `rhizobium-leguminosarum` | gram | neg | neg | [negative](https://bacdive.dsmz.de/strain/138443) |
| `vibrio-cholerae` | gram | neg | neg | [negative](https://bacdive.dsmz.de/strain/130763) |
| `vibrio-cholerae` | oxy | fac | fac | [facultative anaerobe](https://bacdive.dsmz.de/strain/130763) |
| `bacillus-subtilis` | shape | rod | rod | [rod-shaped](https://bacdive.dsmz.de/strain/1172) |
| `bacillus-subtilis` | gram | pos | pos | [positive](https://bacdive.dsmz.de/strain/1172) |
| `lactobacillus-acidophilus` | shape | rod | rod | [rod-shaped](https://bacdive.dsmz.de/strain/6404) |
| `lactobacillus-acidophilus` | gram | pos | pos | [positive](https://bacdive.dsmz.de/strain/6404) |
| `staphylococcus-aureus` | shape | coccus | coccus | [coccus-shaped](https://bacdive.dsmz.de/strain/14487) |
| `staphylococcus-aureus` | gram | pos | pos | [positive](https://bacdive.dsmz.de/strain/14487) |
| `staphylococcus-aureus` | oxy | fac | fac | [facultative anaerobe](https://bacdive.dsmz.de/strain/14487) |
| `streptomyces-griseus` | gram | pos | pos | [positive](https://bacdive.dsmz.de/strain/16229) |
| `streptomyces-griseus` | oxy | aer | aer | [obligate aerobe](https://bacdive.dsmz.de/strain/16229) |
| `streptococcus-pneumoniae` | shape | coccus | coccus | [coccus-shaped](https://bacdive.dsmz.de/strain/14749) |
| `streptococcus-pneumoniae` | gram | pos | pos | [positive](https://bacdive.dsmz.de/strain/14749) |
| `salmonella-enterica` | shape | rod | rod | [rod-shaped](https://bacdive.dsmz.de/strain/5117) |
| `salmonella-enterica` | gram | neg | neg | [negative](https://bacdive.dsmz.de/strain/5117) |
| `helicobacter-pylori` | gram | neg | neg | [negative](https://bacdive.dsmz.de/strain/6102) |
| `helicobacter-pylori` | oxy | low | low | [microaerophile](https://bacdive.dsmz.de/strain/6102) |
| `bacillus-thuringiensis` | shape | rod | rod | [rod-shaped](https://bacdive.dsmz.de/strain/1006) |
| `bacillus-thuringiensis` | gram | pos | pos | [positive](https://bacdive.dsmz.de/strain/1006) |
| `bacillus-thuringiensis` | oxy | fac | fac | [facultative anaerobe](https://bacdive.dsmz.de/strain/1006) |
| `acetobacter-aceti` | shape | rod | rod | [rod-shaped](https://bacdive.dsmz.de/strain/2) |
| `acetobacter-aceti` | gram | neg | neg | [negative](https://bacdive.dsmz.de/strain/2) |
| `acetobacter-aceti` | oxy | aer | aer | [aerobe](https://bacdive.dsmz.de/strain/2) |

## เราว่างแต่ API มี (27)

| ชนิด | ลักษณะ | ของเรา | API | ค่าดิบและแหล่ง |
| --- | --- | --- | --- | --- |
| `halobacterium-salinarum` | temp | — | 37 °C | [2 รายการ](https://bacdive.dsmz.de/strain/5912) |
| `methanobrevibacter-smithii` | temp | — | 37 °C | [2 รายการ](https://bacdive.dsmz.de/strain/6963) |
| `pyrococcus-furiosus` | temp | — | 95–97 °C | [2 รายการ](https://bacdive.dsmz.de/strain/16854) |
| `sulfolobus-acidocaldarius` | temp | — | 70 °C | [2 รายการ](https://bacdive.dsmz.de/strain/16649) |
| `nitrosopumilus-maritimus` | temp | — | 15–35 °C | [2 รายการ](https://bacdive.dsmz.de/strain/141102) |
| `nitrosopumilus-maritimus` | ph | — | 6.8–8.1 pH | [2 รายการ](https://bacdive.dsmz.de/strain/141102) |
| `nitrosopumilus-maritimus` | salinity | — | 32–37 % NaCl | [1 รายการ](https://bacdive.dsmz.de/strain/141102) |
| `methanosarcina-barkeri` | temp | — | 35–37 °C | [2 รายการ](https://bacdive.dsmz.de/strain/7087) |
| `methanocaldococcus-jannaschii` | temp | — | 80 °C | [2 รายการ](https://bacdive.dsmz.de/strain/6981) |
| `haloferax-volcanii` | temp | — | 37 °C | [2 รายการ](https://bacdive.dsmz.de/strain/5933) |
| `thermoplasma-acidophilum` | temp | — | 55 °C | [2 รายการ](https://bacdive.dsmz.de/strain/17017) |
| `escherichia-coli` | motility | — | (ยังแปลงเป็นค่าของเราไม่ได้) yes | [yes](https://bacdive.dsmz.de/strain/4907) |
| `escherichia-coli` | topt | — | meso | [optimum 37 °C](https://bacdive.dsmz.de/strain/4907) |
| `rhizobium-leguminosarum` | motility | — | (ยังแปลงเป็นค่าของเราไม่ได้) yes | [yes](https://bacdive.dsmz.de/strain/138443) |
| `vibrio-cholerae` | motility | — | (ยังแปลงเป็นค่าของเราไม่ได้) yes | [yes](https://bacdive.dsmz.de/strain/130763) |
| `bacillus-subtilis` | motility | — | (ยังแปลงเป็นค่าของเราไม่ได้) yes | [yes](https://bacdive.dsmz.de/strain/1172) |
| `bacillus-subtilis` | endospore | — | yes | [yes](https://bacdive.dsmz.de/strain/1172) |
| `bacillus-subtilis` | topt | — | meso | [optimum 30 °C](https://bacdive.dsmz.de/strain/1172) |
| `lactobacillus-acidophilus` | motility | — | none | [no](https://bacdive.dsmz.de/strain/6404) |
| `staphylococcus-aureus` | motility | — | none | [no](https://bacdive.dsmz.de/strain/14487) |
| `staphylococcus-aureus` | topt | — | meso | [optimum 37 °C](https://bacdive.dsmz.de/strain/14487) |
| `streptomyces-griseus` | motility | — | none | [no](https://bacdive.dsmz.de/strain/16229) |
| `streptococcus-pneumoniae` | motility | — | none | [no](https://bacdive.dsmz.de/strain/14749) |
| `salmonella-enterica` | motility | — | (ยังแปลงเป็นค่าของเราไม่ได้) yes | [yes](https://bacdive.dsmz.de/strain/5117) |
| `bacillus-thuringiensis` | motility | — | none | [no](https://bacdive.dsmz.de/strain/1006) |
| `bacillus-thuringiensis` | endospore | — | yes | [yes](https://bacdive.dsmz.de/strain/1006) |
| `acetobacter-aceti` | motility | — | none | [no](https://bacdive.dsmz.de/strain/2) |

## ต่างกัน (7)

| ชนิด | ลักษณะ | ของเรา | API | ค่าดิบและแหล่ง |
| --- | --- | --- | --- | --- |
| `vibrio-cholerae` | shape | curved | rod | [rod-shaped](https://bacdive.dsmz.de/strain/130763) |
| `bacillus-subtilis` | oxy | aer | fac | [facultative anaerobe](https://bacdive.dsmz.de/strain/1172) |
| `lactobacillus-acidophilus` | oxy | low | ana | [anaerobe](https://bacdive.dsmz.de/strain/6404) |
| `streptomyces-griseus` | shape | filament | rod | [rod-shaped](https://bacdive.dsmz.de/strain/16229) |
| `streptococcus-pneumoniae` | oxy | fac | low | [microaerophile](https://bacdive.dsmz.de/strain/14749) |
| `salmonella-enterica` | oxy | fac | aer | [aerobe](https://bacdive.dsmz.de/strain/5117) |
| `helicobacter-pylori` | shape | curved | rod | [rod-shaped](https://bacdive.dsmz.de/strain/6102) |

## API ไม่มี (48)

| ชนิด | ลักษณะ | ของเรา | API | ค่าดิบและแหล่ง |
| --- | --- | --- | --- | --- |
| `halobacterium-salinarum` | oxy | aer | — | [None](https://bacdive.dsmz.de/strain/5912) |
| `methanobrevibacter-smithii` | shape | rod | — | [None](https://bacdive.dsmz.de/strain/6963) |
| `pyrococcus-furiosus` | shape | coccus | — | [None](https://bacdive.dsmz.de/strain/16854) |
| `sulfolobus-acidocaldarius` | shape | lobed | — | [None](https://bacdive.dsmz.de/strain/16649) |
| `sulfolobus-acidocaldarius` | oxy | aer | — | [None](https://bacdive.dsmz.de/strain/16649) |
| `methanosarcina-barkeri` | shape | coccus | — | [None](https://bacdive.dsmz.de/strain/7087) |
| `methanocaldococcus-jannaschii` | shape | coccus | — | [None](https://bacdive.dsmz.de/strain/6981) |
| `haloferax-volcanii` | shape | irregular | — | [None](https://bacdive.dsmz.de/strain/5933) |
| `haloferax-volcanii` | oxy | aer | — | [None](https://bacdive.dsmz.de/strain/5933) |
| `thermoplasma-acidophilum` | shape | irregular | — | [None](https://bacdive.dsmz.de/strain/17017) |
| `thermoplasma-acidophilum` | oxy | fac | — | [None](https://bacdive.dsmz.de/strain/17017) |
| `rhizobium-leguminosarum` | oxy | aer | — | [None](https://bacdive.dsmz.de/strain/138443) |
| `arthrospira-platensis` | shape | filament | — |  |
| `arthrospira-platensis` | gram | neg | — |  |
| `arthrospira-platensis` | oxy | aer | — |  |
| `nostoc-commune` | shape | filament | — |  |
| `nostoc-commune` | gram | neg | — |  |
| `nostoc-commune` | oxy | aer | — |  |
| `mycobacterium-tuberculosis` | shape | rod | — | [None](https://bacdive.dsmz.de/strain/170314) |
| `mycobacterium-tuberculosis` | gram | none | — | [None](https://bacdive.dsmz.de/strain/170314) |
| `mycobacterium-tuberculosis` | oxy | aer | — | [None](https://bacdive.dsmz.de/strain/170314) |
| `treponema-pallidum` | shape | spiral | — |  |
| `treponema-pallidum` | gram | none | — |  |
| `treponema-pallidum` | oxy | low | — |  |
| `oscillatoria-princeps` | shape | filament | — |  |
| `oscillatoria-princeps` | gram | neg | — |  |
| `oscillatoria-princeps` | oxy | aer | — |  |
| `agrobacterium-tumefaciens` | shape | rod | — |  |
| `agrobacterium-tumefaciens` | gram | neg | — |  |
| `agrobacterium-tumefaciens` | oxy | aer | — |  |
| `clostridium-botulinum` | shape | rod | — | [None](https://bacdive.dsmz.de/strain/166627) |
| `clostridium-botulinum` | gram | pos | — | [None](https://bacdive.dsmz.de/strain/166627) |
| `clostridium-botulinum` | oxy | ana | — | [None](https://bacdive.dsmz.de/strain/166627) |
| `burkholderia-pseudomallei` | shape | rod | — | [None](https://bacdive.dsmz.de/strain/168104) |
| `burkholderia-pseudomallei` | gram | neg | — | [None](https://bacdive.dsmz.de/strain/168104) |
| `burkholderia-pseudomallei` | oxy | aer | — | [None](https://bacdive.dsmz.de/strain/168104) |
| `leptospira-interrogans` | shape | spiral | — | [None](https://bacdive.dsmz.de/strain/168824) |
| `leptospira-interrogans` | gram | none | — | [None](https://bacdive.dsmz.de/strain/168824) |
| `leptospira-interrogans` | oxy | aer | — | [None](https://bacdive.dsmz.de/strain/168824) |
| `thermus-aquaticus` | shape | rod | — | [None](https://bacdive.dsmz.de/strain/16714) |
| `thermus-aquaticus` | gram | neg | — | [None](https://bacdive.dsmz.de/strain/16714) |
| `thermus-aquaticus` | oxy | aer | — | [None](https://bacdive.dsmz.de/strain/16714) |
| `nitrosomonas-europaea` | shape | rod | — | [None](https://bacdive.dsmz.de/strain/130472) |
| `nitrosomonas-europaea` | gram | neg | — | [None](https://bacdive.dsmz.de/strain/130472) |
| `nitrosomonas-europaea` | oxy | aer | — | [None](https://bacdive.dsmz.de/strain/130472) |
| `nitrobacter-winogradskyi` | shape | rod | — | [None](https://bacdive.dsmz.de/strain/1796) |
| `nitrobacter-winogradskyi` | gram | neg | — | [None](https://bacdive.dsmz.de/strain/1796) |
| `nitrobacter-winogradskyi` | oxy | aer | — | [None](https://bacdive.dsmz.de/strain/1796) |

## ชนิดที่ไม่มีระเบียนจาก API

| ชนิด | แหล่ง | เหตุผล |
| --- | --- | --- |
| `spongilla-lacustris` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `aurelia-aurita` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `hydra-vulgaris` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `opisthorchis-viverrini` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `caenorhabditis-elegans` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `hirudinaria-manillensis` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `pomacea-canaliculata` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `nautilus-pompilius` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `aedes-aegypti` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `penaeus-monodon` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `heterometrus-laoticus` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `acanthaster-planci` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `branchiostoma-belcheri` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `betta-splendens` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `hoplobatrachus-rugulosus` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `elephas-maximus` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `dugesia-japonica` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `taenia-solium` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `ascaris-lumbricoides` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `gnathostoma-spinigerum` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `perinereis-nuntia` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `tridacna-squamosa` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `periplaneta-americana` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `drosophila-melanogaster` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `bombyx-mori` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `diadema-setosum` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `ciona-intestinalis` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `rhincodon-typus` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `chelonia-mydas` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `gallus-gallus` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `homo-sapiens` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `ornithorhynchus-anatinus` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `lumbricus-terrestris` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `anopheles-minimus` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `apis-cerana` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `mus-musculus` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `danio-rerio` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `hippocampus-kuda` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `arthrospira-platensis` | bacdive | ไม่พบชื่อนี้ใน BacDive |
| `nostoc-commune` | bacdive | ไม่พบชื่อนี้ใน BacDive |
| `treponema-pallidum` | bacdive | พบ 1 สายพันธุ์แต่ไม่มี type strain ของชื่อนี้ |
| `oscillatoria-princeps` | bacdive | ไม่พบชื่อนี้ใน BacDive |
| `agrobacterium-tumefaciens` | bacdive | พบ 3 สายพันธุ์แต่ไม่มี type strain ของชื่อนี้ (type strain ที่พบเป็นของ Agrobacterium radiobacter ไม่ใช้ ไม่เดา) |
| `sphagnum-palustre` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `marchantia-polymorpha` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `lycopodiella-cernua` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `psilotum-nudum` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `azolla-pinnata` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `cycas-siamensis` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `ginkgo-biloba` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `pinus-kesiya` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `gnetum-gnemon` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `oryza-sativa` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `nelumbo-nucifera` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `durio-zibethinus` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `hevea-brasiliensis` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `anthoceros-punctatus` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `selaginella-involvens` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `equisetum-debile` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `diplazium-esculentum` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `zea-mays` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `mimosa-pudica` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `arabidopsis-thaliana` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `rafflesia-kerrii` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `welwitschia-mirabilis` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `allium-cepa` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `pisum-sativum` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `hydrilla-verticillata` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `ananas-comosus` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `saccharum-officinarum` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `wolffia-globosa` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `nepenthes-mirabilis` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
| `rhizophora-apiculata` | iucn | ยังไม่ได้ดึง: IUCN ปฏิเสธ token (HTTP 401) |
