# ปัญหาใน seed (พบตอนเฟส 1)

ไม่ได้แก้เนื้อหาข้อมูล (`seed/` และ `data/` ยังตรงกับต้นฉบับทุกไบต์)

ตรวจด้วย `python scripts/microsearch.py validate` กับ `data/` ที่นำเข้าจาก seed:
ชนิดทั้ง 145 ชนิดผ่านทุกกฎ (schema, id, lineage, traits, tags, reading_th, ชื่อใน lineage มีใน taxa.json)
ปัญหาเดียวที่พบคือข้อ 1 ด้านล่าง (เดิม 18 error) แก้ด้วยการผ่อนกฎแล้ว ตอนนี้ได้ 0 error

## 1. ชื่อใหม่ของไฟลัม 9 ชื่อใน taxa.json ไม่มี about_th / about_en

กฎ validate: ชื่อใน `taxa.json` ที่ไม่ใช่ genus ต้องมี `about_th` และ `about_en`
ทั้ง 9 รายการมี `rank: null` และ about ว่างทั้งสองภาษา ไม่มีรายการไหนอยู่ใน lineage ของชนิดใดเลย
(lineage ใช้ชื่อเดิม เช่น Proteobacteria) ดูเหมือนเป็นชื่อใหม่จาก `groups.json > phyla[].new_name` ที่ใส่ไว้แสดงคู่กับชื่อตำรา

| ชื่อ | มาจาก (ชื่อตำรา) | กลุ่ม |
| --- | --- | --- |
| Pseudomonadota | Proteobacteria | bacteria |
| Bacillota | Firmicutes | bacteria |
| Cyanobacteriota | Cyanobacteria | bacteria |
| Actinomycetota | Actinobacteria | bacteria |
| Spirochaetota | Spirochaetes | bacteria |
| Deinococcota | Deinococcus-Thermus | bacteria |
| Thermoproteota | Crenarchaeota | archaea |
| Nitrososphaerota | Thaumarchaeota | archaea |
| Mucoromycota | Zygomycota | fungi |

**ตัดสินแล้ว (13 พ.ย. 2026): ผ่อนกฎ** ชื่อที่ `rank` เป็น `null` (ชื่อใหม่ที่ใช้แสดงคู่กับชื่อตำรา) ไม่ต้องมี about
ข้อมูลไม่ถูกแก้ ถ้าเฟส 5 ต้องการเติมคำอธิบายให้ชื่อเหล่านี้ ให้เสนอผู้ใช้ก่อน
(`rank` เป็นสตริงว่างยังนับเป็น "ไม่ใช่สกุล" และต้องมี about)

## สิ่งที่ไม่ใช่ข้อผิดพลาด แต่ควรรู้
- `lineage.rank` ของโพรทิสต์ใช้ `major_clade` (ขีดล่าง) ส่วน `groups.json > ranks` เขียน "Major clade" validate แปลงให้ตรงกันอัตโนมัติ
- `batrachochytrium-dendrobatidis` ใช้ `?` ที่ขั้นวงศ์ (ยอมรับได้ตามกติกา)
- `halobacterium-salinarum` มีช่อง `extra_th`/`extra_en` ที่ชนิดอื่นไม่มี schema อนุญาตเป็นช่องไม่บังคับ
- `images`, `taxon_ids` ว่างทั้งหมด (ตามที่ seed README ระบุ)
