# ความครบของเนื้อหา 8 ส่วนของหน้าชนิด

สร้างจาก `python scripts/microsearch.py coverage` ตัวเลขคือ **จำนวนชนิดที่มีส่วนนั้นแล้ว** (เต็ม = จำนวนชนิดของกลุ่ม)

เกณฑ์ว่า "มี": ส่วน 1 มี `authority`; ส่วน 3 มีแถวลักษณะรวม >= 6 (ลักษณะเลือก + ข้อความลักษณะ + `traitsExtra`); ส่วน 7 ต้องมีทั้ง `name` และ `aside`; ส่วน 8 มี `refs` >= 2 รายการ; ส่วนอื่นมีข้อมูลไม่ว่าง ส่วน 1 และ 8 ใช้ร่วมกันทั้งสองภาษา

## ต่อกลุ่ม: ภาษาไทย

| กลุ่ม | ชนิด | 1 หัวเรื่อง | 2 รู้จักใน 30 วินาที | 3 ลักษณะเด่น | 4 การดำรงชีวิต | 5 วงชีวิต | 6 ความสำคัญ | 7 ชื่อและเกร็ด | 8 อ้างอิง |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bacteria | 24 | 24 | 24 | 24 | 24 | 4 | 24 | 21 | 24 |
| archaea | 9 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 |
| fungi | 19 | 1 | 1 | 0 | 1 | 1 | 1 | 0 | 1 |
| protists | 25 | 21 | 25 | 13 | 25 | 12 | 23 | 1 | 25 |
| plants | 30 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 1 |
| animals | 38 | 1 | 1 | 38 | 1 | 1 | 1 | 0 | 1 |
| **รวม** | 145 | 49 | 53 | 77 | 53 | 18 | 51 | 23 | 53 |

## ต่อกลุ่ม: ภาษาอังกฤษ

| กลุ่ม | ชนิด | 1 หัวเรื่อง | 2 รู้จักใน 30 วินาที | 3 ลักษณะเด่น | 4 การดำรงชีวิต | 5 วงชีวิต | 6 ความสำคัญ | 7 ชื่อและเกร็ด | 8 อ้างอิง |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bacteria | 24 | 24 | 0 | 9 | 0 | 0 | 0 | 0 | 24 |
| archaea | 9 | 1 | 1 | 1 | 0 | 0 | 1 | 1 | 1 |
| fungi | 19 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| protists | 25 | 21 | 0 | 4 | 0 | 0 | 0 | 0 | 25 |
| plants | 30 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| animals | 38 | 1 | 0 | 38 | 0 | 0 | 0 | 0 | 1 |
| **รวม** | 145 | 49 | 1 | 53 | 0 | 0 | 1 | 1 | 53 |

## ต่อชนิด: ภาษาไทย

ตาราง: ✓ มีแล้ว, – ยังไม่มี

| ชนิด | title | lede | traits | life | lifecycle | why | name | refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `spongilla-lacustris` | – | – | ✓ | – | – | – | – | – |
| `aurelia-aurita` | – | – | ✓ | – | – | – | – | – |
| `hydra-vulgaris` | – | – | ✓ | – | – | – | – | – |
| `opisthorchis-viverrini` | – | – | ✓ | – | – | – | – | – |
| `caenorhabditis-elegans` | – | – | ✓ | – | – | – | – | – |
| `hirudinaria-manillensis` | – | – | ✓ | – | – | – | – | – |
| `pomacea-canaliculata` | – | – | ✓ | – | – | – | – | – |
| `nautilus-pompilius` | – | – | ✓ | – | – | – | – | – |
| `aedes-aegypti` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ |
| `penaeus-monodon` | – | – | ✓ | – | – | – | – | – |
| `heterometrus-laoticus` | – | – | ✓ | – | – | – | – | – |
| `acanthaster-planci` | – | – | ✓ | – | – | – | – | – |
| `branchiostoma-belcheri` | – | – | ✓ | – | – | – | – | – |
| `betta-splendens` | – | – | ✓ | – | – | – | – | – |
| `hoplobatrachus-rugulosus` | – | – | ✓ | – | – | – | – | – |
| `elephas-maximus` | – | – | ✓ | – | – | – | – | – |
| `dugesia-japonica` | – | – | ✓ | – | – | – | – | – |
| `taenia-solium` | – | – | ✓ | – | – | – | – | – |
| `ascaris-lumbricoides` | – | – | ✓ | – | – | – | – | – |
| `gnathostoma-spinigerum` | – | – | ✓ | – | – | – | – | – |
| `perinereis-nuntia` | – | – | ✓ | – | – | – | – | – |
| `tridacna-squamosa` | – | – | ✓ | – | – | – | – | – |
| `periplaneta-americana` | – | – | ✓ | – | – | – | – | – |
| `drosophila-melanogaster` | – | – | ✓ | – | – | – | – | – |
| `bombyx-mori` | – | – | ✓ | – | – | – | – | – |
| `diadema-setosum` | – | – | ✓ | – | – | – | – | – |
| `ciona-intestinalis` | – | – | ✓ | – | – | – | – | – |
| `rhincodon-typus` | – | – | ✓ | – | – | – | – | – |
| `chelonia-mydas` | – | – | ✓ | – | – | – | – | – |
| `gallus-gallus` | – | – | ✓ | – | – | – | – | – |
| `homo-sapiens` | – | – | ✓ | – | – | – | – | – |
| `ornithorhynchus-anatinus` | – | – | ✓ | – | – | – | – | – |
| `lumbricus-terrestris` | – | – | ✓ | – | – | – | – | – |
| `anopheles-minimus` | – | – | ✓ | – | – | – | – | – |
| `apis-cerana` | – | – | ✓ | – | – | – | – | – |
| `mus-musculus` | – | – | ✓ | – | – | – | – | – |
| `danio-rerio` | – | – | ✓ | – | – | – | – | – |
| `hippocampus-kuda` | – | – | ✓ | – | – | – | – | – |
| `halobacterium-salinarum` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `methanobrevibacter-smithii` | – | – | – | – | – | – | – | – |
| `pyrococcus-furiosus` | – | – | – | – | – | – | – | – |
| `sulfolobus-acidocaldarius` | – | – | – | – | – | – | – | – |
| `nitrosopumilus-maritimus` | – | – | – | – | – | – | – | – |
| `methanosarcina-barkeri` | – | – | – | – | – | – | – | – |
| `methanocaldococcus-jannaschii` | – | – | – | – | – | – | – | – |
| `haloferax-volcanii` | – | – | – | – | – | – | – | – |
| `thermoplasma-acidophilum` | – | – | – | – | – | – | – | – |
| `escherichia-coli` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `rhizobium-leguminosarum` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `vibrio-cholerae` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `bacillus-subtilis` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `lactobacillus-acidophilus` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `staphylococcus-aureus` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `arthrospira-platensis` | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ |
| `nostoc-commune` | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ |
| `streptomyces-griseus` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `mycobacterium-tuberculosis` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `treponema-pallidum` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `oscillatoria-princeps` | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ |
| `streptococcus-pneumoniae` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `agrobacterium-tumefaciens` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `clostridium-botulinum` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `salmonella-enterica` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `helicobacter-pylori` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `burkholderia-pseudomallei` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `leptospira-interrogans` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `thermus-aquaticus` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `bacillus-thuringiensis` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `nitrosomonas-europaea` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `nitrobacter-winogradskyi` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `acetobacter-aceti` | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| `batrachochytrium-dendrobatidis` | – | – | – | – | – | – | – | – |
| `rhizopus-stolonifer` | – | – | – | – | – | – | – | – |
| `rhizophagus-irregularis` | – | – | – | – | – | – | – | – |
| `saccharomyces-cerevisiae` | ✓ | ✓ | – | ✓ | ✓ | ✓ | – | ✓ |
| `penicillium-chrysogenum` | – | – | – | – | – | – | – | – |
| `aspergillus-oryzae` | – | – | – | – | – | – | – | – |
| `volvariella-volvacea` | – | – | – | – | – | – | – | – |
| `cryptococcus-neoformans` | – | – | – | – | – | – | – | – |
| `neurospora-crassa` | – | – | – | – | – | – | – | – |
| `aspergillus-flavus` | – | – | – | – | – | – | – | – |
| `pleurotus-ostreatus` | – | – | – | – | – | – | – | – |
| `termitomyces-fuliginosus` | – | – | – | – | – | – | – | – |
| `candida-albicans` | – | – | – | – | – | – | – | – |
| `cordyceps-militaris` | – | – | – | – | – | – | – | – |
| `puccinia-graminis` | – | – | – | – | – | – | – | – |
| `pneumocystis-jirovecii` | – | – | – | – | – | – | – | – |
| `aspergillus-niger` | – | – | – | – | – | – | – | – |
| `ganoderma-lucidum` | – | – | – | – | – | – | – | – |
| `amanita-exitialis` | – | – | – | – | – | – | – | – |
| `sphagnum-palustre` | – | – | – | – | – | – | – | – |
| `marchantia-polymorpha` | – | – | – | – | – | – | – | – |
| `lycopodiella-cernua` | – | – | – | – | – | – | – | – |
| `psilotum-nudum` | – | – | – | – | – | – | – | – |
| `azolla-pinnata` | – | – | – | – | – | – | – | – |
| `cycas-siamensis` | – | – | – | – | – | – | – | – |
| `ginkgo-biloba` | – | – | – | – | – | – | – | – |
| `pinus-kesiya` | – | – | – | – | – | – | – | – |
| `gnetum-gnemon` | – | – | – | – | – | – | – | – |
| `oryza-sativa` | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ |
| `nelumbo-nucifera` | – | – | – | – | – | – | – | – |
| `durio-zibethinus` | – | – | – | – | – | – | – | – |
| `hevea-brasiliensis` | – | – | – | – | – | – | – | – |
| `anthoceros-punctatus` | – | – | – | – | – | – | – | – |
| `selaginella-involvens` | – | – | – | – | – | – | – | – |
| `equisetum-debile` | – | – | – | – | – | – | – | – |
| `diplazium-esculentum` | – | – | – | – | – | – | – | – |
| `zea-mays` | – | – | – | – | – | – | – | – |
| `mimosa-pudica` | – | – | – | – | – | – | – | – |
| `arabidopsis-thaliana` | – | – | – | – | – | – | – | – |
| `rafflesia-kerrii` | – | – | – | – | – | – | – | – |
| `welwitschia-mirabilis` | – | – | – | – | – | – | – | – |
| `allium-cepa` | – | – | – | – | – | – | – | – |
| `pisum-sativum` | – | – | – | – | – | – | – | – |
| `hydrilla-verticillata` | – | – | – | – | – | – | – | – |
| `ananas-comosus` | – | – | – | – | – | – | – | – |
| `saccharum-officinarum` | – | – | – | – | – | – | – | – |
| `wolffia-globosa` | – | – | – | – | – | – | – | – |
| `nepenthes-mirabilis` | – | – | – | – | – | – | – | – |
| `rhizophora-apiculata` | – | – | – | – | – | – | – | – |
| `euglena-gracilis` | ✓ | ✓ | – | ✓ | – | ✓ | – | ✓ |
| `trypanosoma-brucei` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ |
| `giardia-intestinalis` | – | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ |
| `paramecium-caudatum` | ✓ | ✓ | – | ✓ | – | ✓ | – | ✓ |
| `plasmodium-falciparum` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `thalassiosira-pseudonana` | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ |
| `chlamydomonas-reinhardtii` | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ |
| `pyropia-yezoensis` | ✓ | ✓ | – | ✓ | ✓ | ✓ | – | ✓ |
| `amoeba-proteus` | ✓ | ✓ | – | ✓ | – | ✓ | – | ✓ |
| `physarum-polycephalum` | ✓ | ✓ | – | ✓ | ✓ | ✓ | – | ✓ |
| `noctiluca-scintillans` | ✓ | ✓ | – | ✓ | ✓ | ✓ | – | ✓ |
| `sargassum-polycystum` | ✓ | ✓ | – | ✓ | – | – | – | ✓ |
| `spirogyra-varians` | ✓ | ✓ | – | ✓ | – | ✓ | – | ✓ |
| `volvox-carteri` | – | ✓ | ✓ | ✓ | – | ✓ | – | ✓ |
| `entamoeba-histolytica` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ |
| `trichomonas-vaginalis` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ |
| `leishmania-donovani` | – | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ |
| `toxoplasma-gondii` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ |
| `dictyostelium-discoideum` | ✓ | ✓ | – | ✓ | ✓ | ✓ | – | ✓ |
| `phytophthora-infestans` | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ |
| `chlorella-vulgaris` | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ |
| `caulerpa-lentillifera` | ✓ | ✓ | – | ✓ | – | – | – | ✓ |
| `gracilaria-fisheri` | – | ✓ | – | ✓ | – | ✓ | – | ✓ |
| `plasmodium-vivax` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ |
| `vorticella-campanula` | ✓ | ✓ | – | ✓ | – | ✓ | – | ✓ |

## ต่อชนิด: ภาษาอังกฤษ

ตาราง: ✓ มีแล้ว, – ยังไม่มี

| ชนิด | title | lede | traits | life | lifecycle | why | name | refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `spongilla-lacustris` | – | – | ✓ | – | – | – | – | – |
| `aurelia-aurita` | – | – | ✓ | – | – | – | – | – |
| `hydra-vulgaris` | – | – | ✓ | – | – | – | – | – |
| `opisthorchis-viverrini` | – | – | ✓ | – | – | – | – | – |
| `caenorhabditis-elegans` | – | – | ✓ | – | – | – | – | – |
| `hirudinaria-manillensis` | – | – | ✓ | – | – | – | – | – |
| `pomacea-canaliculata` | – | – | ✓ | – | – | – | – | – |
| `nautilus-pompilius` | – | – | ✓ | – | – | – | – | – |
| `aedes-aegypti` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `penaeus-monodon` | – | – | ✓ | – | – | – | – | – |
| `heterometrus-laoticus` | – | – | ✓ | – | – | – | – | – |
| `acanthaster-planci` | – | – | ✓ | – | – | – | – | – |
| `branchiostoma-belcheri` | – | – | ✓ | – | – | – | – | – |
| `betta-splendens` | – | – | ✓ | – | – | – | – | – |
| `hoplobatrachus-rugulosus` | – | – | ✓ | – | – | – | – | – |
| `elephas-maximus` | – | – | ✓ | – | – | – | – | – |
| `dugesia-japonica` | – | – | ✓ | – | – | – | – | – |
| `taenia-solium` | – | – | ✓ | – | – | – | – | – |
| `ascaris-lumbricoides` | – | – | ✓ | – | – | – | – | – |
| `gnathostoma-spinigerum` | – | – | ✓ | – | – | – | – | – |
| `perinereis-nuntia` | – | – | ✓ | – | – | – | – | – |
| `tridacna-squamosa` | – | – | ✓ | – | – | – | – | – |
| `periplaneta-americana` | – | – | ✓ | – | – | – | – | – |
| `drosophila-melanogaster` | – | – | ✓ | – | – | – | – | – |
| `bombyx-mori` | – | – | ✓ | – | – | – | – | – |
| `diadema-setosum` | – | – | ✓ | – | – | – | – | – |
| `ciona-intestinalis` | – | – | ✓ | – | – | – | – | – |
| `rhincodon-typus` | – | – | ✓ | – | – | – | – | – |
| `chelonia-mydas` | – | – | ✓ | – | – | – | – | – |
| `gallus-gallus` | – | – | ✓ | – | – | – | – | – |
| `homo-sapiens` | – | – | ✓ | – | – | – | – | – |
| `ornithorhynchus-anatinus` | – | – | ✓ | – | – | – | – | – |
| `lumbricus-terrestris` | – | – | ✓ | – | – | – | – | – |
| `anopheles-minimus` | – | – | ✓ | – | – | – | – | – |
| `apis-cerana` | – | – | ✓ | – | – | – | – | – |
| `mus-musculus` | – | – | ✓ | – | – | – | – | – |
| `danio-rerio` | – | – | ✓ | – | – | – | – | – |
| `hippocampus-kuda` | – | – | ✓ | – | – | – | – | – |
| `halobacterium-salinarum` | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | ✓ |
| `methanobrevibacter-smithii` | – | – | – | – | – | – | – | – |
| `pyrococcus-furiosus` | – | – | – | – | – | – | – | – |
| `sulfolobus-acidocaldarius` | – | – | – | – | – | – | – | – |
| `nitrosopumilus-maritimus` | – | – | – | – | – | – | – | – |
| `methanosarcina-barkeri` | – | – | – | – | – | – | – | – |
| `methanocaldococcus-jannaschii` | – | – | – | – | – | – | – | – |
| `haloferax-volcanii` | – | – | – | – | – | – | – | – |
| `thermoplasma-acidophilum` | – | – | – | – | – | – | – | – |
| `escherichia-coli` | ✓ | – | – | – | – | – | – | ✓ |
| `rhizobium-leguminosarum` | ✓ | – | – | – | – | – | – | ✓ |
| `vibrio-cholerae` | ✓ | – | – | – | – | – | – | ✓ |
| `bacillus-subtilis` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `lactobacillus-acidophilus` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `staphylococcus-aureus` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `arthrospira-platensis` | ✓ | – | – | – | – | – | – | ✓ |
| `nostoc-commune` | ✓ | – | – | – | – | – | – | ✓ |
| `streptomyces-griseus` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `mycobacterium-tuberculosis` | ✓ | – | – | – | – | – | – | ✓ |
| `treponema-pallidum` | ✓ | – | – | – | – | – | – | ✓ |
| `oscillatoria-princeps` | ✓ | – | – | – | – | – | – | ✓ |
| `streptococcus-pneumoniae` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `agrobacterium-tumefaciens` | ✓ | – | – | – | – | – | – | ✓ |
| `clostridium-botulinum` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `salmonella-enterica` | ✓ | – | – | – | – | – | – | ✓ |
| `helicobacter-pylori` | ✓ | – | – | – | – | – | – | ✓ |
| `burkholderia-pseudomallei` | ✓ | – | – | – | – | – | – | ✓ |
| `leptospira-interrogans` | ✓ | – | – | – | – | – | – | ✓ |
| `thermus-aquaticus` | ✓ | – | – | – | – | – | – | ✓ |
| `bacillus-thuringiensis` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `nitrosomonas-europaea` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `nitrobacter-winogradskyi` | ✓ | – | – | – | – | – | – | ✓ |
| `acetobacter-aceti` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `batrachochytrium-dendrobatidis` | – | – | – | – | – | – | – | – |
| `rhizopus-stolonifer` | – | – | – | – | – | – | – | – |
| `rhizophagus-irregularis` | – | – | – | – | – | – | – | – |
| `saccharomyces-cerevisiae` | ✓ | – | – | – | – | – | – | ✓ |
| `penicillium-chrysogenum` | – | – | – | – | – | – | – | – |
| `aspergillus-oryzae` | – | – | – | – | – | – | – | – |
| `volvariella-volvacea` | – | – | – | – | – | – | – | – |
| `cryptococcus-neoformans` | – | – | – | – | – | – | – | – |
| `neurospora-crassa` | – | – | – | – | – | – | – | – |
| `aspergillus-flavus` | – | – | – | – | – | – | – | – |
| `pleurotus-ostreatus` | – | – | – | – | – | – | – | – |
| `termitomyces-fuliginosus` | – | – | – | – | – | – | – | – |
| `candida-albicans` | – | – | – | – | – | – | – | – |
| `cordyceps-militaris` | – | – | – | – | – | – | – | – |
| `puccinia-graminis` | – | – | – | – | – | – | – | – |
| `pneumocystis-jirovecii` | – | – | – | – | – | – | – | – |
| `aspergillus-niger` | – | – | – | – | – | – | – | – |
| `ganoderma-lucidum` | – | – | – | – | – | – | – | – |
| `amanita-exitialis` | – | – | – | – | – | – | – | – |
| `sphagnum-palustre` | – | – | – | – | – | – | – | – |
| `marchantia-polymorpha` | – | – | – | – | – | – | – | – |
| `lycopodiella-cernua` | – | – | – | – | – | – | – | – |
| `psilotum-nudum` | – | – | – | – | – | – | – | – |
| `azolla-pinnata` | – | – | – | – | – | – | – | – |
| `cycas-siamensis` | – | – | – | – | – | – | – | – |
| `ginkgo-biloba` | – | – | – | – | – | – | – | – |
| `pinus-kesiya` | – | – | – | – | – | – | – | – |
| `gnetum-gnemon` | – | – | – | – | – | – | – | – |
| `oryza-sativa` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `nelumbo-nucifera` | – | – | – | – | – | – | – | – |
| `durio-zibethinus` | – | – | – | – | – | – | – | – |
| `hevea-brasiliensis` | – | – | – | – | – | – | – | – |
| `anthoceros-punctatus` | – | – | – | – | – | – | – | – |
| `selaginella-involvens` | – | – | – | – | – | – | – | – |
| `equisetum-debile` | – | – | – | – | – | – | – | – |
| `diplazium-esculentum` | – | – | – | – | – | – | – | – |
| `zea-mays` | – | – | – | – | – | – | – | – |
| `mimosa-pudica` | – | – | – | – | – | – | – | – |
| `arabidopsis-thaliana` | – | – | – | – | – | – | – | – |
| `rafflesia-kerrii` | – | – | – | – | – | – | – | – |
| `welwitschia-mirabilis` | – | – | – | – | – | – | – | – |
| `allium-cepa` | – | – | – | – | – | – | – | – |
| `pisum-sativum` | – | – | – | – | – | – | – | – |
| `hydrilla-verticillata` | – | – | – | – | – | – | – | – |
| `ananas-comosus` | – | – | – | – | – | – | – | – |
| `saccharum-officinarum` | – | – | – | – | – | – | – | – |
| `wolffia-globosa` | – | – | – | – | – | – | – | – |
| `nepenthes-mirabilis` | – | – | – | – | – | – | – | – |
| `rhizophora-apiculata` | – | – | – | – | – | – | – | – |
| `euglena-gracilis` | ✓ | – | – | – | – | – | – | ✓ |
| `trypanosoma-brucei` | ✓ | – | – | – | – | – | – | ✓ |
| `giardia-intestinalis` | – | – | – | – | – | – | – | ✓ |
| `paramecium-caudatum` | ✓ | – | – | – | – | – | – | ✓ |
| `plasmodium-falciparum` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `thalassiosira-pseudonana` | ✓ | – | – | – | – | – | – | ✓ |
| `chlamydomonas-reinhardtii` | ✓ | – | – | – | – | – | – | ✓ |
| `pyropia-yezoensis` | ✓ | – | – | – | – | – | – | ✓ |
| `amoeba-proteus` | ✓ | – | – | – | – | – | – | ✓ |
| `physarum-polycephalum` | ✓ | – | – | – | – | – | – | ✓ |
| `noctiluca-scintillans` | ✓ | – | – | – | – | – | – | ✓ |
| `sargassum-polycystum` | ✓ | – | – | – | – | – | – | ✓ |
| `spirogyra-varians` | ✓ | – | – | – | – | – | – | ✓ |
| `volvox-carteri` | – | – | – | – | – | – | – | ✓ |
| `entamoeba-histolytica` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `trichomonas-vaginalis` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `leishmania-donovani` | – | – | – | – | – | – | – | ✓ |
| `toxoplasma-gondii` | ✓ | – | – | – | – | – | – | ✓ |
| `dictyostelium-discoideum` | ✓ | – | – | – | – | – | – | ✓ |
| `phytophthora-infestans` | ✓ | – | – | – | – | – | – | ✓ |
| `chlorella-vulgaris` | ✓ | – | – | – | – | – | – | ✓ |
| `caulerpa-lentillifera` | ✓ | – | – | – | – | – | – | ✓ |
| `gracilaria-fisheri` | – | – | – | – | – | – | – | ✓ |
| `plasmodium-vivax` | ✓ | – | ✓ | – | – | – | – | ✓ |
| `vorticella-campanula` | ✓ | – | – | – | – | – | – | ✓ |
