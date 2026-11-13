# Microsearch 2.0 — คำสั่งสำหรับ AI ประจำ repo

เว็บความรู้เรื่องสิ่งมีชีวิต 6 กลุ่ม (แบคทีเรีย อาร์เคีย ฟังไจ โพรทิสต์ พืช สัตว์) สำหรับนักเรียน ม.ปลาย และนักศึกษา
ไทย/อังกฤษ เป็น static site บน GitHub Pages ใช้โครงเดียวกับ repo `nexus-cells`
แผนเต็มอยู่ที่ `docs/plan.md` (อนุมัติแล้ว 13 พ.ย. 2026) อ่านก่อนเริ่มงานทุกเฟส

## ไฟล์อ้างอิงที่ห้ามเข้าใจผิด

- `design/prototype.html` คือ **แบบที่อนุมัติแล้ว** เว็บจริงต้องหน้าตาและพฤติกรรมเหมือนต้นแบบ ไม่แก้ต้นแบบ
  ถ้าเห็นว่าควรเปลี่ยนให้เสนอผู้ใช้ก่อน
- `seed/` คือ **ข้อมูลตั้งต้น** (145 ชนิด, 490 ชื่อในแผนผัง, ทุกรายการ `review: ai_draft`) **ห้ามแก้ตรงๆ**
  ให้นำเข้าไป `data/` ด้วยสคริปต์ (เฟส 1) แล้วแก้ที่ `data/` เท่านั้น
- (ตอนเริ่มเฟส 0 ทั้งสองอย่างนี้ยังต้องวางลงในโฟลเดอร์ ถ้าไม่พบให้แจ้งผู้ใช้ อย่าสร้างขึ้นเอง)

## โครงโฟลเดอร์

```
docs/plan.md              แผนและบันทึกการตัดสินใจ
design/prototype.html     ต้นแบบที่อนุมัติแล้ว (อ่านอย่างเดียว)
seed/                     ข้อมูลตั้งต้นจากต้นแบบ (อ่านอย่างเดียว)
schema/*.schema.json      JSON Schema ของ organism, taxon, groups
data/groups.json          กลุ่ม ลำดับขั้น ลักษณะ แท็ก (นำเข้าจาก seed)
data/taxa.json            ทุกชื่อในแผนผัง (นำเข้าจาก seed)
data/organisms/<group>.json  145 ชนิด แยกต่อกลุ่ม
data/generated/           ไฟล์ที่สคริปต์สร้าง (taxa-fetched.json จาก fetch)
cache/                    คำตอบดิบจาก GBIF/NCBI (อยู่ใน .gitignore)
reports/                  รายงานจากสคริปต์ (taxonomy-diff.md, seed-issues.md) screens/ ไม่ commit
scripts/microsearch.py    เครื่องมือหลักตัวเดียว
site/                     หน้าเว็บที่ deploy
  index.html, css/style.css, js/*.js (ES modules ไม่ใช้ framework: router, diagram, search, filters, query), js/views/
  i18n/th.json, en.json   ข้อความ UI ทั้งหมด (ห้ามฝังข้อความไทยใน JS)
  data/*.json             สร้างจาก build ห้ามแก้เอง ไม่อยู่ใน repo
tests/                    pytest (validate, fetch, build)
tests/e2e/                puppeteer: pages.mjs (npm test), screens.mjs (npm run screens)
.github/workflows/deploy.yml  validate -> pytest -> build -> e2e -> deploy Pages
```

## คำสั่งที่ใช้

บนเครื่อง Windows ของผู้ใช้ `python` ใน Git Bash เป็น stub ให้ใช้ `py` แทน (บน CI ใช้ `python`)

```bash
python scripts/microsearch.py import-seed [--force]   # seed/ -> data/ (ไม่ทับไฟล์ที่แก้แล้ว)
python scripts/microsearch.py validate                # ตรวจข้อมูล ต้อง 0 error ก่อน deploy
python scripts/microsearch.py fetch [--only id,..] [--refresh]   # GBIF + NCBI (cache ใน cache/)
python scripts/microsearch.py taxonomy-diff           # reports/taxonomy-diff.md
python scripts/microsearch.py build                   # validate แล้วสร้าง site/data/*.json
python -m pytest tests                                # ทดสอบสคริปต์
npm test                                              # e2e ทั้งหมด = test:pages + test:diagram + test:search (build ให้เอง)
npm run test:pages                                    # ทุกหน้า x ไทย/อังกฤษ ไม่มี console error ไม่มีไทยหลุดในโหมดอังกฤษ
npm run test:diagram                                  # คลิกทุกชื่อในแผนผังทั้ง 6 กลุ่ม x 2 ภาษา
npm run test:search                                   # ชุดคำค้นตายตัว วัดเวลา (<100 ms) ตัวกรองใน URL
npm run screens                                       # screenshot เทียบต้นแบบ 1440px/390px
python scripts/microsearch.py images                  # ตรวจรูป เครดิต license (เฟส 6 ยังไม่มี)
python scripts/microsearch.py coverage                # ช่องอังกฤษที่ยังว่างต่อกลุ่ม -> reports/coverage.md
npm run test:offline                                  # ทดสอบ PWA ออฟไลน์ (เฟส 7 ยังไม่มี)
```

Python 3 stdlib เท่านั้น (pytest ใช้เฉพาะตอนทดสอบ) Node ใช้เฉพาะงานทดสอบ ระบุเวอร์ชันแน่นอนใน package.json
ต้องมี Chrome หรือ Edge สำหรับ `npm test` (ตั้ง `CHROME_PATH` ถ้าอยู่ที่อื่น)

## ทำเสมอ

- ไทย + อังกฤษ ทุกเนื้อหา (summary_en, traits_text_en ต้องครบ validate เตือนถ้าว่าง) ส่วน name_en คือชื่อสามัญภาษาอังกฤษ **ว่างได้** ถ้าไม่มีชื่อสามัญจริง ห้ามแต่งชื่อ
- ทุกรูปมีเครดิตและ license (ไฟล์ ≤500 KB)
- ไม่เดา taxon ID: หาไม่เจอให้เป็น `null` แล้วลงรายงานใน `reports/`
- `validate` ต้องผ่านก่อน deploy
- เนื้อหาที่ Claude ร่างติด `review: ai_draft` และเว็บแสดง "ร่างโดย AI รอตรวจทาน"
- เฟส 2 ทำแค่รายงานเทียบลำดับชั้น **ไม่แก้ข้อมูลเอง** ผู้ใช้อนุมัติก่อนแก้ในเฟส 5
- ชื่อไฟลัมตามตำรา แสดงชื่อใหม่คู่กัน; ป้ายระดับ `hs` / `uni`
- แหล่งตรวจอนุกรมวิธาน: GBIF API + NCBI E-utilities (≤3 คำขอ/วินาที) ไม่ใช้ LPSN
- โพรทิสต์จัดตามซูเปอร์กรุ๊ปที่เขียนเองใน `groups.json`

## ไม่ทำ

- ไวรัส
- ระบบสมาชิก
- แชท AI
- แก้ repo `microsearch` เดิม หรือนำข้อมูลเดิมมาใช้
- ไม่เขียนข้อความไทยใน JS (ใช้ `site/i18n/*.json`)
- รายการที่ "ยังไม่ได้กำหนด" ใน docs/plan.md (จำนวนชนิดหลังเปิดตัว, คำอ่านไทย/ศัพท์บัญญัติที่ต้องเทียบราชบัณฑิตยสภา) ให้ถามผู้ใช้ ไม่ตัดสินเอง

## Project Hub

โปรเจกต์นี้ลงทะเบียนใน Project Hub (https://kl3korawit777-ai.github.io/project-hub/) ชื่อ "Microsearch 2.0"
อัปเดตผ่าน `python ~/.project-hub/hub_agent.py <คำสั่ง>` (Windows: `C:\Users\kl3ko\.project-hub\hub_agent.py`)
รันจากใน repo นี้เพื่อให้หา `.hub.env` เจอ ค่า `HUB_URL`, `HUB_KEY`, `HUB_TOKEN` อยู่ใน `.hub.env`
(อยู่ใน `.gitignore` แล้ว) **ห้ามขอ token ในแชท และห้ามพิมพ์ token ออกแชท log หรือไฟล์อื่น**
token ผูกกับโปรเจกต์นี้โปรเจกต์เดียว ห้ามใช้ token ของโปรเจกต์อื่น (เช่น nexus-cells)

คำสั่ง (ต่อท้าย `--json` ถ้าต้องการผลดิบ):
- `status` ดูข้อมูล ขั้นตอน (มีเลขลำดับ) และอัปเดตล่าสุด
- `log "ข้อความ" [--version vX.Y]` บันทึกความคืบหน้า 1 รายการ
- `done <เลขลำดับ|คำในชื่อ>` / `undone ...` ติ๊ก / ยกเลิกติ๊กขั้นตอน
- `add-milestone "ชื่อ" [--due YYYY-MM-DD]`
- `set key=value ...` แก้ได้เฉพาะ status tagline tags start_date end_date web_url github_url folder_path

กติกา:
- ก่อนเริ่มงานใหญ่ ให้รัน `status`
- เมื่อทำงานเสร็จเป็นชิ้น (จบเฟส ฟีเจอร์ใช้ได้ deploy) ให้ `log` 1 รายการ ภาษาไทยในมุมของผลลัพธ์ วันละไม่เกิน 2–3 รายการ
  (จำกัด 20 รายการ/ชั่วโมง) ใส่ `--version` เฉพาะตอนออกเวอร์ชันจริง
- ติ๊ก `done` ก็ต่อเมื่อใช้งานได้จริงและทดสอบแล้ว ไม่แน่ใจให้ถามผู้ใช้
- งานที่ไม่ตรงกับขั้นตอนที่มี ให้เสนอ `add-milestone` แล้วรอผู้ใช้ตอบก่อนเพิ่ม
- `set web_url` / `github_url` ได้เมื่อ deploy หรือสร้าง repo ใหม่ ส่วน status และวันที่ต้องถามผู้ใช้ก่อนเปลี่ยน
- ลบ/เปลี่ยนชื่อโปรเจกต์ไม่ได้ อย่าพยายามหลบข้อจำกัด
- ถ้าคำสั่งผิดพลาด (ขึ้นต้นด้วยรหัส เช่น `invalid_token:` `rate_limited:`) แจ้งผู้ใช้แล้วทำงานหลักต่อ ห้ามลองซ้ำวน

## ข้อตกลง commit

- commit ข้อความท้ายด้วย `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`
- ไม่ใส่อีเมลหรือข้อมูลส่วนตัวของผู้ใช้ในคำขอไปบริการภายนอกใดๆ
