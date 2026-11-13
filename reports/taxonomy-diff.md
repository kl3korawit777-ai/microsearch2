# รายงานเทียบลำดับชั้นกับ GBIF และ NCBI

สร้างจาก `python scripts/microsearch.py taxonomy-diff` (ข้อมูลดิบ `data/generated/taxa-fetched.json`)
รายงานนี้ **ไม่แก้ข้อมูลอัตโนมัติ** ผู้ใช้ตัดสินก่อนแก้ในเฟส 5

## สรุป

| หมวด | จำนวนชนิด |
| --- | --- |
| ต่างกันจริง | 70 |
| ชื่อใหม่ของชื่อเดียวกัน | 7 |
| หาไม่เจอ | 0 |
| ตรงกันหมด | 68 |
| รวม | 145 จาก 145 |

วิธีเทียบ:
- เทียบชื่อของเราทีละขั้นกับชื่อที่ API ให้ในขั้นเดียวกัน ถ้า API ไม่มีขั้นนั้น (เช่น NCBI ใช้ no rank) ดูว่ามีชื่อของเราอยู่ที่ใดในลำดับชั้นของ API หรือไม่ ถ้าไม่มีเลยถือว่าเทียบไม่ได้ ไม่นับเป็นความต่าง
- ซูเปอร์กรุ๊ปของโพรทิสต์ไม่เทียบ (ไม่มีใน API) เทียบเฉพาะกลุ่มหลัก กลุ่มย่อย และสกุล
- ชื่อที่นับว่าเป็นของเดียวกันตามธรรมเนียม ไม่ถือเป็นความต่าง: Eukarya = Eukaryota, Plantae = Viridiplantae, Animalia = Metazoa
- ชื่อไฟลัมตามตำราที่ตั้งใจใช้คู่กับชื่อใหม่ใน `groups.json` จัดเป็น "ชื่อใหม่ของชื่อเดียวกัน" ไม่ใช่ความต่างจริง
- ชนิดที่ GBIF/NCBI ไม่พบ (หรือเป็น FUZZY/HIGHERRANK) ใช้ id เป็น null ไม่เดา
- ชนิดที่พบแหล่งเดียว (10 ชนิด) เทียบกับแหล่งที่พบ: clostridium-botulinum, helicobacter-pylori, nitrobacter-winogradskyi, equisetum-debile, streptococcus-pneumoniae, trichomonas-vaginalis, leishmania-donovani, gracilaria-fisheri, plasmodium-vivax, vorticella-campanula

## ต่างกันจริง (70 ชนิด)

| ชนิด | ลำดับขั้น | ของเรา | GBIF | NCBI | ข้อเสนอ |
| --- | --- | --- | --- | --- | --- |
| *Opisthorchis viverrini* (animals) | order | Opisthorchiida | Plagiorchiida | Opisthorchiida | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Hirudinaria manillensis* (animals) | order | Arhynchobdellida | Arhynchobdellida | Hirudinida | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Betta splendens* (animals) | class | Actinopterygii | — | Actinopteri | ตรวจเอง (มีแหล่งเดียว: NCBI) |
| *Betta splendens* (animals) | order | Anabantiformes | Perciformes | Anabantiformes | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Rhincodon typus* (animals) | class | Chondrichthyes | Elasmobranchii | Chondrichthyes | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Chelonia mydas* (animals) | class | Reptilia | Testudines | — | ตรวจเอง (มีแหล่งเดียว: GBIF) |
| *Danio rerio* (animals) | class | Actinopterygii | — | Actinopteri | ตรวจเอง (มีแหล่งเดียว: NCBI) |
| *Danio rerio* (animals) | family | Danionidae | Cyprinidae | Danionidae | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Hippocampus kuda* (animals) | class | Actinopterygii | — | Actinopteri | ตรวจเอง (มีแหล่งเดียว: NCBI) |
| *Halobacterium salinarum* (archaea) | phylum | Euryarchaeota | Halobacteriota | Methanobacteriota | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Methanobrevibacter smithii* (archaea) | phylum | Euryarchaeota | Methanobacteriota | Methanobacteriota | เสนอเปลี่ยนเป็น Methanobacteriota (GBIF และ NCBI ตรงกัน) |
| *Pyrococcus furiosus* (archaea) | phylum | Euryarchaeota | Methanobacteriota | Methanobacteriota | เสนอเปลี่ยนเป็น Methanobacteriota (GBIF และ NCBI ตรงกัน) |
| *Sulfolobus acidocaldarius* (archaea) | phylum | Crenarchaeota | Thermoproteota | Thermoproteota | คงชื่อตำรา Crenarchaeota แสดงชื่อใหม่ Thermoproteota คู่กัน (ตามที่ตั้งใจ) |
| *Sulfolobus acidocaldarius* (archaea) | class | Thermoprotei | Thermoproteia | Thermoprotei | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Nitrosopumilus maritimus* (archaea) | phylum | Thaumarchaeota | Thermoproteota | Nitrososphaerota | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Nitrosopumilus maritimus* (archaea) | order | Nitrosopumilales | Nitrososphaerales | Nitrosopumilales | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Methanosarcina barkeri* (archaea) | phylum | Euryarchaeota | Halobacteriota | Methanobacteriota | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Methanosarcina barkeri* (archaea) | class | Methanomicrobia | Methanosarcinia | Methanomicrobia | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Methanocaldococcus jannaschii* (archaea) | phylum | Euryarchaeota | Methanobacteriota | Methanobacteriota | เสนอเปลี่ยนเป็น Methanobacteriota (GBIF และ NCBI ตรงกัน) |
| *Haloferax volcanii* (archaea) | phylum | Euryarchaeota | Halobacteriota | Methanobacteriota | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Haloferax volcanii* (archaea) | order | Haloferacales | Halobacteriales | Halobacteriales | เสนอเปลี่ยนเป็น Halobacteriales (GBIF และ NCBI ตรงกัน) |
| *Thermoplasma acidophilum* (archaea) | phylum | Euryarchaeota | Thermoplasmatota | Thermoplasmatota | เสนอเปลี่ยนเป็น Thermoplasmatota (GBIF และ NCBI ตรงกัน) |
| *Rhizobium leguminosarum* (bacteria) | phylum | Proteobacteria | Proteobacteria | Pseudomonadota | คงชื่อตำรา Proteobacteria แสดงชื่อใหม่ Pseudomonadota คู่กัน (ตามที่ตั้งใจ) |
| *Rhizobium leguminosarum* (bacteria) | order | Rhizobiales | Rhizobiales | Hyphomicrobiales | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Vibrio cholerae* (bacteria) | phylum | Proteobacteria | Proteobacteria | Pseudomonadota | คงชื่อตำรา Proteobacteria แสดงชื่อใหม่ Pseudomonadota คู่กัน (ตามที่ตั้งใจ) |
| *Vibrio cholerae* (bacteria) | order | Vibrionales | Enterobacterales | Vibrionales | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Bacillus subtilis* (bacteria) | phylum | Firmicutes | Firmicutes | Bacillota | คงชื่อตำรา Firmicutes แสดงชื่อใหม่ Bacillota คู่กัน (ตามที่ตั้งใจ) |
| *Bacillus subtilis* (bacteria) | order | Bacillales | Bacillales | Caryophanales | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Staphylococcus aureus* (bacteria) | phylum | Firmicutes | Firmicutes | Bacillota | คงชื่อตำรา Firmicutes แสดงชื่อใหม่ Bacillota คู่กัน (ตามที่ตั้งใจ) |
| *Staphylococcus aureus* (bacteria) | order | Bacillales | Staphylococcales | Caryophanales | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Arthrospira platensis* (bacteria) | phylum | Cyanobacteria | Cyanobacteria | Cyanobacteriota | คงชื่อตำรา Cyanobacteria แสดงชื่อใหม่ Cyanobacteriota คู่กัน (ตามที่ตั้งใจ) |
| *Arthrospira platensis* (bacteria) | class | Cyanophyceae | Cyanobacteriia | Cyanophyceae | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Arthrospira platensis* (bacteria) | order | Oscillatoriales | Cyanobacteriales | Oscillatoriales | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Arthrospira platensis* (bacteria) | family | Microcoleaceae | Microcoleaceae | Sirenicapillariaceae | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Arthrospira platensis* (bacteria) | genus | Arthrospira | Arthrospira | Limnospira | ชื่อเปลี่ยนเป็น Limnospira (เสนอ: ตัดสินในเฟส 5) |
| *Arthrospira platensis* (bacteria) | species | Arthrospira platensis | Arthrospira platensis | Limnospira platensis | ชื่อที่ยอมรับตอนนี้คือ Limnospira platensis (เสนอ: ตัดสินในเฟส 5) |
| *Nostoc commune* (bacteria) | phylum | Cyanobacteria | Cyanobacteria | Cyanobacteriota | คงชื่อตำรา Cyanobacteria แสดงชื่อใหม่ Cyanobacteriota คู่กัน (ตามที่ตั้งใจ) |
| *Nostoc commune* (bacteria) | class | Cyanophyceae | Cyanobacteriia | Cyanophyceae | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Nostoc commune* (bacteria) | order | Nostocales | Cyanobacteriales | Nostocales | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Streptomyces griseus* (bacteria) | phylum | Actinobacteria | Actinobacteriota | Actinomycetota | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Streptomyces griseus* (bacteria) | class | Actinomycetes | Actinomycetia | Actinomycetes | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Streptomyces griseus* (bacteria) | order | Streptomycetales | Streptomycetales | Kitasatosporales | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Mycobacterium tuberculosis* (bacteria) | phylum | Actinobacteria | Actinobacteriota | Actinomycetota | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Mycobacterium tuberculosis* (bacteria) | class | Actinomycetes | Actinomycetia | Actinomycetes | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Treponema pallidum* (bacteria) | phylum | Spirochaetes | Spirochaetota | Spirochaetota | คงชื่อตำรา Spirochaetes แสดงชื่อใหม่ Spirochaetota คู่กัน (ตามที่ตั้งใจ) |
| *Treponema pallidum* (bacteria) | order | Spirochaetales | Treponematales | Treponematales | เสนอเปลี่ยนเป็น Treponematales (GBIF และ NCBI ตรงกัน) |
| *Oscillatoria princeps* (bacteria) | phylum | Cyanobacteria | Cyanobacteria | Cyanobacteriota | คงชื่อตำรา Cyanobacteria แสดงชื่อใหม่ Cyanobacteriota คู่กัน (ตามที่ตั้งใจ) |
| *Oscillatoria princeps* (bacteria) | class | Cyanophyceae | Cyanobacteriia | Cyanophyceae | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Oscillatoria princeps* (bacteria) | order | Oscillatoriales | Cyanobacteriales | Oscillatoriales | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Agrobacterium tumefaciens* (bacteria) | phylum | Proteobacteria | Proteobacteria | Pseudomonadota | คงชื่อตำรา Proteobacteria แสดงชื่อใหม่ Pseudomonadota คู่กัน (ตามที่ตั้งใจ) |
| *Agrobacterium tumefaciens* (bacteria) | order | Rhizobiales | Rhizobiales | Hyphomicrobiales | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Clostridium botulinum* (bacteria) | phylum | Firmicutes | — | Bacillota | คงชื่อตำรา Firmicutes แสดงชื่อใหม่ Bacillota คู่กัน (ตามที่ตั้งใจ) |
| *Clostridium botulinum* (bacteria) | order | Clostridiales | — | Eubacteriales | ตรวจเอง (มีแหล่งเดียว: NCBI) |
| *Helicobacter pylori* (bacteria) | phylum | Proteobacteria | — | Campylobacterota | ตรวจเอง (มีแหล่งเดียว: NCBI) |
| *Burkholderia pseudomallei* (bacteria) | phylum | Proteobacteria | Proteobacteria | Pseudomonadota | คงชื่อตำรา Proteobacteria แสดงชื่อใหม่ Pseudomonadota คู่กัน (ตามที่ตั้งใจ) |
| *Burkholderia pseudomallei* (bacteria) | class | Betaproteobacteria | Gammaproteobacteria | Betaproteobacteria | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Burkholderia pseudomallei* (bacteria) | species | Burkholderia pseudomallei | Burkholderia mallei | Burkholderia pseudomallei | ชื่อที่ยอมรับตอนนี้คือ Burkholderia mallei (เสนอ: ตัดสินในเฟส 5) |
| *Leptospira interrogans* (bacteria) | phylum | Spirochaetes | Spirochaetota | Spirochaetota | คงชื่อตำรา Spirochaetes แสดงชื่อใหม่ Spirochaetota คู่กัน (ตามที่ตั้งใจ) |
| *Leptospira interrogans* (bacteria) | class | Spirochaetia | Leptospirae | Leptospiria | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Thermus aquaticus* (bacteria) | phylum | Deinococcus-Thermus | Deinococcota | Deinococcota | คงชื่อตำรา Deinococcus-Thermus แสดงชื่อใหม่ Deinococcota คู่กัน (ตามที่ตั้งใจ) |
| *Thermus aquaticus* (bacteria) | order | Thermales | Deinococcales | Thermales | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Bacillus thuringiensis* (bacteria) | phylum | Firmicutes | Firmicutes | Bacillota | คงชื่อตำรา Firmicutes แสดงชื่อใหม่ Bacillota คู่กัน (ตามที่ตั้งใจ) |
| *Bacillus thuringiensis* (bacteria) | order | Bacillales | Bacillales | Caryophanales | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Nitrosomonas europaea* (bacteria) | phylum | Proteobacteria | Proteobacteria | Pseudomonadota | คงชื่อตำรา Proteobacteria แสดงชื่อใหม่ Pseudomonadota คู่กัน (ตามที่ตั้งใจ) |
| *Nitrosomonas europaea* (bacteria) | class | Betaproteobacteria | Gammaproteobacteria | Betaproteobacteria | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Nitrosomonas europaea* (bacteria) | order | Nitrosomonadales | Burkholderiales | Nitrosomonadales | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Nitrobacter winogradskyi* (bacteria) | phylum | Proteobacteria | — | Pseudomonadota | คงชื่อตำรา Proteobacteria แสดงชื่อใหม่ Pseudomonadota คู่กัน (ตามที่ตั้งใจ) |
| *Nitrobacter winogradskyi* (bacteria) | order | Rhizobiales | — | Hyphomicrobiales | ตรวจเอง (มีแหล่งเดียว: NCBI) |
| *Acetobacter aceti* (bacteria) | phylum | Proteobacteria | Proteobacteria | Pseudomonadota | คงชื่อตำรา Proteobacteria แสดงชื่อใหม่ Pseudomonadota คู่กัน (ตามที่ตั้งใจ) |
| *Acetobacter aceti* (bacteria) | order | Rhodospirillales | Acetobacterales | Acetobacterales | เสนอเปลี่ยนเป็น Acetobacterales (GBIF และ NCBI ตรงกัน) |
| *Batrachochytrium dendrobatidis* (fungi) | class | Chytridiomycetes | Rhizophydiomycetes | Chytridiomycetes | ตรวจเอง (GBIF ต่าง อีกแหล่งตรงกับเรา) |
| *Rhizopus stolonifer* (fungi) | phylum | Zygomycota | Mucoromycota | Mucoromycota | คงชื่อตำรา Zygomycota แสดงชื่อใหม่ Mucoromycota คู่กัน (ตามที่ตั้งใจ) |
| *Rhizopus stolonifer* (fungi) | family | Mucoraceae | Rhizopodaceae | Rhizopodaceae | เสนอเปลี่ยนเป็น Rhizopodaceae (GBIF และ NCBI ตรงกัน) |
| *Candida albicans* (fungi) | class | Saccharomycetes | Saccharomycetes | Pichiomycetes | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Candida albicans* (fungi) | order | Saccharomycetales | Saccharomycetales | Serinales | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Pneumocystis jirovecii* (fungi) | class | Pneumocystidomycetes | Pneumocystomycetes | Pneumocystomycetes | เสนอเปลี่ยนเป็น Pneumocystomycetes (GBIF และ NCBI ตรงกัน) |
| *Pneumocystis jirovecii* (fungi) | order | Pneumocystidales | Pneumocystales | Pneumocystales | เสนอเปลี่ยนเป็น Pneumocystales (GBIF และ NCBI ตรงกัน) |
| *Pneumocystis jirovecii* (fungi) | family | Pneumocystidaceae | Pneumocystaceae | Pneumocystaceae | เสนอเปลี่ยนเป็น Pneumocystaceae (GBIF และ NCBI ตรงกัน) |
| *Sphagnum palustre* (plants) | phylum | Bryophyta | Bryophyta | Streptophyta | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Marchantia polymorpha* (plants) | phylum | Hepatophyta | Marchantiophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Lycopodiella cernua* (plants) | phylum | Lycophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Lycopodiella cernua* (plants) | genus | Lycopodiella | Palhinhaea | Palhinhaea | ชื่อเปลี่ยนเป็น Palhinhaea (เสนอ: ตัดสินในเฟส 5) |
| *Lycopodiella cernua* (plants) | species | Lycopodiella cernua | Palhinhaea cernua | Palhinhaea cernua | ชื่อที่ยอมรับตอนนี้คือ Palhinhaea cernua (เสนอ: ตัดสินในเฟส 5) |
| *Psilotum nudum* (plants) | phylum | Pterophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Psilotum nudum* (plants) | class | Psilotopsida | Polypodiopsida | Polypodiopsida | เสนอเปลี่ยนเป็น Polypodiopsida (GBIF และ NCBI ตรงกัน) |
| *Azolla pinnata* (plants) | phylum | Pterophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Cycas siamensis* (plants) | phylum | Cycadophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Ginkgo biloba* (plants) | phylum | Ginkgophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Pinus kesiya* (plants) | phylum | Coniferophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Gnetum gnemon* (plants) | phylum | Gnetophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Oryza sativa* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Oryza sativa* (plants) | class | Liliopsida | Liliopsida | Magnoliopsida | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Nelumbo nucifera* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Durio zibethinus* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Hevea brasiliensis* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Anthoceros punctatus* (plants) | phylum | Anthocerophyta | Anthocerotophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Selaginella involvens* (plants) | phylum | Lycophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Equisetum debile* (plants) | phylum | Pterophyta | Tracheophyta | — | ตรวจเอง (มีแหล่งเดียว: GBIF) |
| *Diplazium esculentum* (plants) | phylum | Pterophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Zea mays* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Zea mays* (plants) | class | Liliopsida | Liliopsida | Magnoliopsida | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Mimosa pudica* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Arabidopsis thaliana* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Rafflesia kerrii* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Welwitschia mirabilis* (plants) | phylum | Gnetophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Allium cepa* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Allium cepa* (plants) | class | Liliopsida | Liliopsida | Magnoliopsida | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Pisum sativum* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Pisum sativum* (plants) | genus | Pisum | Lathyrus | Lathyrus | ชื่อเปลี่ยนเป็น Lathyrus (เสนอ: ตัดสินในเฟส 5) |
| *Pisum sativum* (plants) | species | Pisum sativum | Lathyrus oleraceus | Lathyrus oleraceus | ชื่อที่ยอมรับตอนนี้คือ Lathyrus oleraceus (เสนอ: ตัดสินในเฟส 5) |
| *Hydrilla verticillata* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Hydrilla verticillata* (plants) | class | Liliopsida | Liliopsida | Magnoliopsida | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Ananas comosus* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Ananas comosus* (plants) | class | Liliopsida | Liliopsida | Magnoliopsida | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Saccharum officinarum* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Saccharum officinarum* (plants) | class | Liliopsida | Liliopsida | Magnoliopsida | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Wolffia globosa* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Wolffia globosa* (plants) | class | Liliopsida | Liliopsida | Magnoliopsida | ตรวจเอง (NCBI ต่าง อีกแหล่งตรงกับเรา) |
| *Nepenthes mirabilis* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |
| *Rhizophora apiculata* (plants) | phylum | Anthophyta | Tracheophyta | Streptophyta | ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน) |

## ชื่อใหม่ของชื่อเดียวกัน (7 ชนิด)

| ชนิด | ลำดับขั้น | ของเรา | GBIF | NCBI | ข้อเสนอ |
| --- | --- | --- | --- | --- | --- |
| *Escherichia coli* (bacteria) | phylum | Proteobacteria | Proteobacteria | Pseudomonadota | คงชื่อตำรา Proteobacteria แสดงชื่อใหม่ Pseudomonadota คู่กัน (ตามที่ตั้งใจ) |
| *Lactobacillus acidophilus* (bacteria) | phylum | Firmicutes | Firmicutes | Bacillota | คงชื่อตำรา Firmicutes แสดงชื่อใหม่ Bacillota คู่กัน (ตามที่ตั้งใจ) |
| *Streptococcus pneumoniae* (bacteria) | phylum | Firmicutes | — | Bacillota | คงชื่อตำรา Firmicutes แสดงชื่อใหม่ Bacillota คู่กัน (ตามที่ตั้งใจ) |
| *Salmonella enterica* (bacteria) | phylum | Proteobacteria | Proteobacteria | Pseudomonadota | คงชื่อตำรา Proteobacteria แสดงชื่อใหม่ Pseudomonadota คู่กัน (ตามที่ตั้งใจ) |
| *Aspergillus oryzae* (fungi) | species | Aspergillus oryzae | Aspergillus flavus | Aspergillus oryzae | ชื่อที่ยอมรับตอนนี้คือ Aspergillus flavus (เสนอ: ตัดสินในเฟส 5) |
| *Giardia intestinalis* (protists) | species | Giardia intestinalis | Giardia duodenalis | Giardia duodenalis | ชื่อที่ยอมรับตอนนี้คือ Giardia duodenalis (เสนอ: ตัดสินในเฟส 5) |
| *Physarum polycephalum* (protists) | genus | Physarum | Physarum | Badhamia | ชื่อเปลี่ยนเป็น Badhamia (เสนอ: ตัดสินในเฟส 5) |
| *Physarum polycephalum* (protists) | species | Physarum polycephalum | Physarum polycephalum | Badhamia polycephala | ชื่อที่ยอมรับตอนนี้คือ Badhamia polycephala (เสนอ: ตัดสินในเฟส 5) |

## หาไม่เจอ (0 ชนิด)


## ตรงกันหมด (68 ชนิด)

| ชนิด | หมายเหตุ |
| --- | --- |
| *Spongilla lacustris* (animals) | — |
| *Aurelia aurita* (animals) | — |
| *Hydra vulgaris* (animals) | — |
| *Caenorhabditis elegans* (animals) | — |
| *Pomacea canaliculata* (animals) | — |
| *Nautilus pompilius* (animals) | — |
| *Aedes aegypti* (animals) | — |
| *Penaeus monodon* (animals) | — |
| *Heterometrus laoticus* (animals) | — |
| *Acanthaster planci* (animals) | — |
| *Branchiostoma belcheri* (animals) | — |
| *Hoplobatrachus rugulosus* (animals) | — |
| *Elephas maximus* (animals) | — |
| *Dugesia japonica* (animals) | เทียบไม่ได้: class |
| *Taenia solium* (animals) | — |
| *Ascaris lumbricoides* (animals) | — |
| *Gnathostoma spinigerum* (animals) | — |
| *Perinereis nuntia* (animals) | — |
| *Tridacna squamosa* (animals) | — |
| *Periplaneta americana* (animals) | — |
| *Drosophila melanogaster* (animals) | — |
| *Bombyx mori* (animals) | — |
| *Diadema setosum* (animals) | — |
| *Ciona intestinalis* (animals) | — |
| *Gallus gallus* (animals) | — |
| *Homo sapiens* (animals) | — |
| *Ornithorhynchus anatinus* (animals) | — |
| *Lumbricus terrestris* (animals) | — |
| *Anopheles minimus* (animals) | — |
| *Apis cerana* (animals) | — |
| *Mus musculus* (animals) | — |
| *Rhizophagus irregularis* (fungi) | — |
| *Saccharomyces cerevisiae* (fungi) | — |
| *Penicillium chrysogenum* (fungi) | — |
| *Volvariella volvacea* (fungi) | — |
| *Cryptococcus neoformans* (fungi) | — |
| *Neurospora crassa* (fungi) | — |
| *Aspergillus flavus* (fungi) | — |
| *Pleurotus ostreatus* (fungi) | — |
| *Termitomyces fuliginosus* (fungi) | — |
| *Cordyceps militaris* (fungi) | — |
| *Puccinia graminis* (fungi) | — |
| *Aspergillus niger* (fungi) | — |
| *Ganoderma lucidum* (fungi) | — |
| *Amanita exitialis* (fungi) | — |
| *Euglena gracilis* (protists) | — |
| *Trypanosoma brucei* (protists) | — |
| *Paramecium caudatum* (protists) | — |
| *Plasmodium falciparum* (protists) | — |
| *Thalassiosira pseudonana* (protists) | เทียบไม่ได้: major_clade |
| *Chlamydomonas reinhardtii* (protists) | — |
| *Pyropia yezoensis* (protists) | — |
| *Amoeba proteus* (protists) | — |
| *Noctiluca scintillans* (protists) | เทียบไม่ได้: subgroup |
| *Sargassum polycystum* (protists) | เทียบไม่ได้: major_clade |
| *Spirogyra varians* (protists) | — |
| *Volvox carteri* (protists) | — |
| *Entamoeba histolytica* (protists) | — |
| *Trichomonas vaginalis* (protists) | ไม่พบใน GBIF |
| *Leishmania donovani* (protists) | ไม่พบใน GBIF |
| *Toxoplasma gondii* (protists) | — |
| *Dictyostelium discoideum* (protists) | — |
| *Phytophthora infestans* (protists) | เทียบไม่ได้: major_clade |
| *Chlorella vulgaris* (protists) | — |
| *Caulerpa lentillifera* (protists) | — |
| *Gracilaria fisheri* (protists) | ไม่พบใน GBIF |
| *Plasmodium vivax* (protists) | ไม่พบใน GBIF |
| *Vorticella campanula* (protists) | ไม่พบใน GBIF |
