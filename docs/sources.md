# แหล่งข้อมูลต่อกลุ่ม

ใช้ในแผนค้นคว้า v1.1 (`docs/content-research-plan.md`) ลิงก์ในตารางเป็นหน้าค้นหาหรือหน้าแรกของแต่ละแหล่ง ใส่ชื่อวิทยาศาสตร์ต่อท้ายหรือค้นในหน้านั้น
ตรวจลิงก์ทุกครั้งที่ใช้งานจริง ถ้าแหล่งเปลี่ยนที่อยู่ให้แก้ที่ไฟล์นี้ที่เดียว กฎการใช้: เขียนใหม่ด้วยคำของเราเอง ไม่คัดลอกประโยค (ดู `docs/content-spec.md`)

## ชื่อ ผู้ตั้งชื่อ ชื่อพ้อง

| กลุ่ม | แหล่ง | หน้าค้นหา | หมายเหตุ |
| --- | --- | --- | --- |
| ทุกกลุ่ม | GBIF | https://www.gbif.org/species/search?q= | มี ID แล้ว ตรวจว่ายังตรง |
| ทุกกลุ่ม | NCBI Taxonomy | https://www.ncbi.nlm.nih.gov/taxonomy | มี ID แล้ว |
| ทุกกลุ่ม | Catalogue of Life | https://www.catalogueoflife.org/data/search?q= | ใช้ตัดสินเมื่อ GBIF กับ NCBI ไม่ตรงกัน |
| แบคทีเรีย อาร์เคีย | LPSN | https://lpsn.dsmz.de/search?word= | เว็บ ไม่มี API |
| ฟังไจ | Index Fungorum | https://www.indexfungorum.org/names/names.asp | |
| ฟังไจ | MycoBank | https://www.mycobank.org/ | |
| โพรทิสต์ | AlgaeBase | https://www.algaebase.org/search/species/ | ใช้หน้าเว็บ ไม่ซื้อ API (ราว 10 ชนิด) |
| โพรทิสต์ สัตว์ (ทะเล) | WoRMS | https://www.marinespecies.org/aphia.php?p=taxlist | |
| พืช | POWO / WCVP | https://powo.science.kew.org/ | |
| สัตว์ | ITIS | https://www.itis.gov/ | |

## ลักษณะมีโครงสร้าง (ค่าใน `groups.json` ใช้กรองได้)

| กลุ่ม | แหล่ง | หน้าค้นหา | หมายเหตุ |
| --- | --- | --- | --- |
| แบคทีเรีย อาร์เคีย | BacDive | https://bacdive.dsmz.de/ | API ฟรีแต่ต้องสมัคร (ผู้ใช้สมัครเอง เฟส R2) |
| ฟังไจ | MycoBank, ตำราราวิทยา | https://www.mycobank.org/ | |
| โพรทิสต์ | AlgaeBase | https://www.algaebase.org/search/species/ | |
| พืช | POWO | https://powo.science.kew.org/ | |
| สัตว์ | Animal Diversity Web | https://animaldiversity.org/search/?q= | |

## เนื้อหาบรรยาย

| กลุ่ม | แหล่ง | หน้าค้นหา | หมายเหตุ |
| --- | --- | --- | --- |
| ทุกกลุ่ม | บทความ review และตำรามหาวิทยาลัย | https://pubmed.ncbi.nlm.nih.gov/?term= | PubMed ค้นบทความ review; ตำราระบุในอ้างอิงตามจริง |
| ทุกกลุ่ม | ราชบัณฑิตยสภา (ศัพท์ไทย) | https://www.royin.go.th/ | เทียบศัพท์ ถ้าไม่แน่ใจให้ถามผู้ใช้ |
| แบคทีเรีย อาร์เคีย (เชื้อก่อโรค) | CDC, WHO fact sheet | https://www.cdc.gov/ , https://www.who.int/news-room/fact-sheets | |
| แบคทีเรีย อาร์เคีย | MicrobeWiki | https://microbewiki.kenyon.edu/index.php?search= | |
| ฟังไจ (ราก่อโรค) | CDC | https://www.cdc.gov/fungal/ | |
| ฟังไจ (เห็ดพิษ) | กรมควบคุมโรค | https://ddc.moph.go.th/ | ยังไม่ได้สำรวจหน้าข้อมูล (R6) |
| โพรทิสต์ (ปรสิต) | CDC DPDx | https://www.cdc.gov/dpdx/ | วงชีวิต |
| พืช | POWO | https://powo.science.kew.org/ | |
| พืช สัตว์ (สถานภาพ) | IUCN Red List | https://www.iucnredlist.org/search?query= | API ฟรีสำหรับการศึกษา ต้องขอ token (ผู้ใช้ขอเอง เฟส R2) ใช้ได้เฉพาะหมวดและลิงก์ |
| สัตว์ | Animal Diversity Web | https://animaldiversity.org/search/?q= | |
| สัตว์ (ปรสิต) | CDC DPDx | https://www.cdc.gov/dpdx/ | |

## บัญชีและ token

BacDive และ IUCN ผู้ใช้สมัครเองและเก็บใน `.env` (ไม่ commit) Claude ไม่ขอ token ในแชทและไม่พิมพ์ token ออกที่ใด
