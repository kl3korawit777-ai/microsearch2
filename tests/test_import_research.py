"""ทดสอบ import-research: อ่านไฟล์พัก ตรวจเทียบฉบับร่างแรก (humanizer ห้ามเปลี่ยนข้อเท็จจริง) แล้วนำเข้าเป็น extra_th"""

import json
import os
import shutil
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, HERE)
import microsearch as ms  # noqa: E402
from test_validate import Dataset, ds, error_codes  # noqa: E402,F401

MD = """# ร่างทดสอบ

## escherichia-coli

### รู้จักใน 30 วินาที
แบคทีเรียรูปท่อน ยาวราว 2 ไมโครเมตร [1] พบในลำไส้ของคน [2]

### การดำรงชีวิต
- แหล่งที่อยู่: ลำไส้ใหญ่ [2]
- การหายใจ: ใช้ออกซิเจนก็ได้ ไม่ใช้ก็ได้
  ต่อบรรทัดที่สอง [1]

### การสืบพันธุ์และวงชีวิต

### ความสำคัญ
- วิทยาศาสตร์: จีโนม K-12 ยาว 4.64 ล้านคู่เบส [1]

### ชื่อนี้มาจากไหน
- Escherichia: ตั้งตามธีโอดอร์ เอเชอริช [2]
- เกร็ด: ชื่อเดิมคือ Bacterium coli commune [2]
- เกร็ด: ได้รับการยอมรับในปี 1958 [1]
"""
DATA = {"escherichia-coli": {
    "authority": "(Migula 1895) Castellani & Chalmers 1919", "synonyms": ["Bacillus coli"], "accepted_name": None, "traits": {},
    "traitsExtra": [["จีโนม", "4.64 ล้านคู่เบส"]], "traitsExtraRefs": [[1]], "asideTitle": "เกร็ดทดสอบ",
    "refs": [{"n": 1, "title": "A", "url": "https://example.org/a", "accessed": "2026-11-14"},
             {"n": 2, "title": "B", "url": "https://example.org/b", "accessed": "2026-11-14"}],
    "iucn": None}}


@pytest.fixture
def world(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    ds.write()
    r = tmp_path / "research"
    r.mkdir()
    (r / "t.md").write_text(MD, encoding="utf-8")
    (r / "t.data.json").write_text(json.dumps(DATA, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "base.md").write_text(MD, encoding="utf-8")
    return ds, tmp_path


def run(world, *extra, md=None, data=None):
    ds, tmp = world
    if md is not None:
        (tmp / "research" / "t.md").write_text(md, encoding="utf-8")
    if data is not None:
        (tmp / "research" / "t.data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    args = ms.build_parser().parse_args(["import-research", str(tmp / "research" / "t"), "--data", ds.root, "--baseline", str(tmp / "base.md"),
                                         "--report", str(tmp / "reports" / "import-check.md"), *extra])
    return ms.cmd_import_research(args)


def ecoli(world):
    ds, _ = world
    return json.load(open(os.path.join(ds.root, "organisms", "bacteria.json"), encoding="utf-8"))[0]


def test_parse_groups_lines_by_species_and_heading():
    got = ms.parse_research_md(MD)
    assert list(got) == ["escherichia-coli"]
    assert list(got["escherichia-coli"]) == ["รู้จักใน 30 วินาที", "การดำรงชีวิต", "การสืบพันธุ์และวงชีวิต", "ความสำคัญ", "ชื่อนี้มาจากไหน"]
    assert got["escherichia-coli"]["การสืบพันธุ์และวงชีวิต"] == []


def test_parse_rejects_duplicates_and_orphan_headings():
    with pytest.raises(ValueError):
        ms.parse_research_md("## a\n## a\n")
    with pytest.raises(ValueError):
        ms.parse_research_md("### รู้จักใน 30 วินาที\nx\n")
    with pytest.raises(ValueError):
        ms.parse_research_md("## a\n### ความสำคัญ\n### ความสำคัญ\n")


def test_dry_run_changes_nothing(world, capsys):
    before = ecoli(world)
    assert run(world, "--dry-run") == 0
    assert ecoli(world) == before
    out = capsys.readouterr().out
    assert "[dry-run] escherichia-coli" in out and "extra_th" in out and "ยังไม่ได้เขียนไฟล์" in out


def test_import_fills_extra_th_and_species_fields(world):
    assert run(world) == 0
    o = ecoli(world)
    ex = o["extra_th"]
    assert list(ex) == ["lede", "traitsExtra", "life", "why", "name", "asideTitle", "aside"]
    assert ex["lede"] == "แบคทีเรียรูปท่อน ยาวราว 2 ไมโครเมตร [1] พบในลำไส้ของคน [2]"
    assert ex["life"] == [["แหล่งที่อยู่", "ลำไส้ใหญ่ [2]"], ["การหายใจ", "ใช้ออกซิเจนก็ได้ ไม่ใช้ก็ได้ ต่อบรรทัดที่สอง [1]"]]   # บรรทัดต่อรวมเป็นแถวเดียว
    assert ex["why"] == [["วิทยาศาสตร์", "จีโนม K-12 ยาว 4.64 ล้านคู่เบส [1]"]]
    assert ex["name"] == [["Escherichia", "ตั้งตามธีโอดอร์ เอเชอริช [2]"]]
    assert ex["aside"] == ["ชื่อเดิมคือ Bacterium coli commune [2]", "ได้รับการยอมรับในปี 1958 [1]"] and ex["asideTitle"] == "เกร็ดทดสอบ"
    assert ex["traitsExtra"] == [["จีโนม", "4.64 ล้านคู่เบส [1]"]]   # เลขอ้างอิงของแถวต่อท้ายข้อความ
    assert "lifecycle" not in ex                                       # หัวข้อว่างไม่สร้างช่อง
    assert o["authority"].startswith("(Migula") and o["synonyms"] == ["Bacillus coli"] and "accepted_name" not in o and "iucn" not in o
    assert o["refs"] == [{"title": "A", "url": "https://example.org/a", "accessed": "2026-11-14"}, {"title": "B", "url": "https://example.org/b", "accessed": "2026-11-14"}]
    assert o["review"] == "ai_draft"
    assert ms.validate_data(world[0].root).errors == []


def test_import_is_idempotent_and_replaces_old_extra(world):
    ds, _ = world
    ds.files["bacteria"][0]["extra_th"] = {"lede": "เก่า", "aside": ["ข้อเก่า"], "asideTitle": "เก่า", "name": [["x", "y"]]}
    ds.write()
    assert run(world) == 0
    first = ecoli(world)
    assert "เก่า" not in json.dumps(first, ensure_ascii=False)
    assert run(world) == 0 and ecoli(world) == first


def test_import_merges_traits_without_dropping_existing(world):
    ds, tmp = world
    data = json.loads(json.dumps(DATA))
    data["escherichia-coli"]["traits"] = {}
    assert run(world, data=data) == 0
    assert ecoli(world)["traits"] == {"shape": "rod"}


def test_disease_and_warning_sections(world):
    ds, _ = world
    ds.files["bacteria"][0]["tags"] = ["science", "medicine"]
    ds.write()
    md = MD + "\n### โรค\n- ชื่อโรค: ท้องเสีย [1]\n- อาการหลัก: ถ่ายเหลว\n- การติดต่อ: อาหารปนเปื้อน\n- การป้องกัน: ล้างมือ\n- กลุ่มยา: ยาปฏิชีวนะบางกลุ่ม\n" \
                 "\n### คำเตือน\n- คำเตือน: ระวัง\n- เข้าใจผิด: ต้มแล้วปลอดภัย\n- เข้าใจผิด: สีสวยกินได้\n"
    (world[1] / "base.md").write_text(md, encoding="utf-8")
    assert run(world, md=md) == 0
    ex = ecoli(world)["extra_th"]
    assert ex["disease"] == {"name": "ท้องเสีย [1]", "symptoms": "ถ่ายเหลว", "transmission": "อาหารปนเปื้อน", "prevention": "ล้างมือ", "drugs": "ยาปฏิชีวนะบางกลุ่ม"}
    assert ex["warning"] == {"text": "ระวัง", "myths": ["ต้มแล้วปลอดภัย", "สีสวยกินได้"]}
    assert ms.validate_data(world[0].root).errors == []


def test_unknown_label_in_disease_stops_without_importing(world):
    md = MD + "\n### โรค\n- ยา: 500 mg\n"
    (world[1] / "base.md").write_text(md, encoding="utf-8")
    before = ecoli(world)
    assert run(world, md=md) == 1 and ecoli(world) == before


@pytest.mark.parametrize("edit,expect", [
    (lambda t: t.replace("### ความสำคัญ\n", ""), "หัวข้อไม่เหมือนเดิม"),
    (lambda t: t.replace("### การสืบพันธุ์และวงชีวิต\n\n", "### การสืบพันธุ์และวงชีวิต\n\n### ความสำคัญ x\n\n").replace("### ความสำคัญ x", "### โรค"), "หัวข้อไม่เหมือนเดิม"),
    (lambda t: t.replace("4.64 ล้านคู่เบส", "4.6 ล้านคู่เบส"), "ตัวเลขและหน่วย"),
    (lambda t: t.replace("ปี 1958", "ปี 1959"), "ตัวเลขและหน่วย"),
    (lambda t: t.replace("2 ไมโครเมตร", "2 มิลลิเมตร"), "ตัวเลขและหน่วย"),
    (lambda t: t.replace("Bacterium coli commune", "Bacterium coli"), "ชื่อวิทยาศาสตร์"),
    (lambda t: t.replace("Escherichia:", "Escherichea:"), "ชื่อวิทยาศาสตร์"),
    (lambda t: t.replace("พบในลำไส้ของคน [2]", "พบในลำไส้ของคน"), "เลขอ้างอิง"),
    (lambda t: t.replace("ลำไส้ใหญ่ [2]", "ลำไส้ใหญ่ [1]"), "เลขอ้างอิง"),
])
def test_check_stops_when_facts_changed_and_writes_report(world, edit, expect):
    before = ecoli(world)
    assert run(world, md=edit(MD)) == 1
    assert ecoli(world) == before                      # ไม่ได้นำเข้าอะไรเลย
    report = (world[1] / "reports" / "import-check.md").read_text(encoding="utf-8")
    assert "ไม่ผ่าน" in report and expect in report and "escherichia-coli" in report


def test_rewording_that_keeps_facts_passes(world):
    reworded = (MD.replace("แบคทีเรียรูปท่อน ยาวราว 2 ไมโครเมตร [1] พบในลำไส้ของคน [2]", "พบในลำไส้ของคน [2] เป็นแบคทีเรียรูปท่อนยาวราว 2 ไมโครเมตร [1]")
                  .replace("ใช้ออกซิเจนก็ได้ ไม่ใช้ก็ได้", "อยู่ได้ทั้งมีและไม่มีออกซิเจน"))
    assert run(world, md=reworded) == 0
    assert ecoli(world)["extra_th"]["lede"].startswith("พบในลำไส้ของคน [2]")


def test_numbers_with_commas_are_compared_as_numbers(world):
    base = MD.replace("4.64 ล้านคู่เบส", "4,640 ล้านคู่เบส")
    (world[1] / "base.md").write_text(base, encoding="utf-8")
    assert run(world, md=base.replace("4,640", "4640")) == 0


def test_refs_must_be_numbered_in_order_and_cover_all_citations(world):
    data = json.loads(json.dumps(DATA))
    data["escherichia-coli"]["refs"][1]["n"] = 3
    assert run(world, data=data) == 1
    data = json.loads(json.dumps(DATA))
    data["escherichia-coli"]["refs"] = data["escherichia-coli"]["refs"][:1]
    assert run(world, data=data) == 1
    assert "[2]" in (world[1] / "reports" / "import-check.md").read_text(encoding="utf-8")


def test_species_missing_in_data_or_json_stops(world):
    assert run(world, md=MD + "\n## no-such-species\n### รู้จักใน 30 วินาที\nx\n") == 1
    ds, tmp = world
    (tmp / "base.md").write_text(MD, encoding="utf-8")
    data = {}
    assert run(world, md=MD, data=data) == 1


def test_missing_required_heading_in_both_versions_still_stops(world):
    md = MD.replace("### การสืบพันธุ์และวงชีวิต\n\n", "")
    (world[1] / "base.md").write_text(md, encoding="utf-8")
    assert run(world, md=md) == 1
    assert "ขาดหัวข้อ" in (world[1] / "reports" / "import-check.md").read_text(encoding="utf-8")


def test_only_limits_the_species(world):
    assert run(world, "--only", "plasmodium-falciparum") == 0
    assert "extra_th" not in ecoli(world)


def test_citation_number_beyond_refs_is_a_validate_error(ds):
    o = ds.files["bacteria"][0]
    o["refs"] = [{"title": "a", "url": "https://x.org", "accessed": "2026-11-14"}]
    o["extra_th"] = {"lede": "ข้อความ [1] และ [2]"}
    rep = ds.check()
    assert "CITE_REF" in error_codes(rep)
    o["extra_th"] = {"lede": "ข้อความ [1]"}
    assert ds.check().errors == []
    del o["refs"]
    assert "CITE_REF" in error_codes(ds.check())


def test_missing_baseline_without_git_history_is_reported(world, capsys, monkeypatch):
    ds, tmp = world
    monkeypatch.setattr(ms, "research_baseline", lambda rel: None)
    args = ms.build_parser().parse_args(["import-research", str(tmp / "research" / "t"), "--data", ds.root])
    assert ms.cmd_import_research(args) == 1
    assert "ฉบับร่างแรก" in capsys.readouterr().out


def test_real_pilot_files_import_cleanly_into_a_copy_of_the_real_data(tmp_path):
    data = tmp_path / "data"
    shutil.copytree(os.path.join(ROOT, "data"), str(data))
    src = os.path.join(ROOT, "research", "pilot")
    args = ms.build_parser().parse_args(["import-research", src, "--data", str(data), "--baseline", src + ".md", "--report", str(tmp_path / "check.md")])
    assert ms.cmd_import_research(args) == 0
    assert ms.validate_data(str(data)).errors == []
    done = {o["id"]: o for o in ms.load_organisms(str(data)) if o.get("extra_th")}
    assert {"escherichia-coli", "halobacterium-salinarum", "saccharomyces-cerevisiae", "plasmodium-falciparum", "oryza-sativa", "aedes-aegypti"} <= set(done)
    pilot = {"escherichia-coli", "halobacterium-salinarum", "saccharomyces-cerevisiae", "plasmodium-falciparum", "oryza-sativa", "aedes-aegypti"}
    assert all(len(done[i]["refs"]) >= 2 and done[i]["authority"] for i in pilot)
    # หัวข้อว่างไม่สร้างช่อง: วงชีวิตของ E. coli ยังไม่มี
    assert "lifecycle" not in done["escherichia-coli"]["extra_th"] and "disease" in done["plasmodium-falciparum"]["extra_th"]
