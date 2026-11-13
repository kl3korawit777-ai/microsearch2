"""ทดสอบคำสั่ง coverage: นับช่องอังกฤษที่ยังว่างต่อกลุ่มและเขียน reports/coverage.md"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
sys.path.insert(0, HERE)
import microsearch as ms  # noqa: E402
from test_validate import Dataset  # noqa: E402


def rows_by_group(ds):
    ds.write()
    rows, gaps = ms.coverage_data(ds.root)
    return {r["id"]: r for r in rows}, gaps


def test_complete_data_has_zero_gaps(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    rows, gaps = rows_by_group(ds)
    assert gaps == {} and all(r["gaps"] == 0 for r in rows.values())
    assert rows["bacteria"]["species"] == 1 and rows["protists"]["species"] == 1


def test_counts_each_kind_of_gap_per_group(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    o = ds.files["bacteria"][0]
    o["summary_en"] = ""
    o["traits_text_th"] = {"food": "อาหาร", "home": "ที่อยู่"}
    o["traits_text_en"] = {"food": "Food"}
    o["extra_th"] = {"lede": "x"}
    rows, gaps = rows_by_group(ds)
    b = rows["bacteria"]
    assert (b["summary_en"], b["traits_text_en"], b["traits_text_total"], b["extra_en"], b["gaps"]) == (1, 1, 2, 1, 3)
    assert gaps["escherichia-coli"] == ["summary_en", "traits_text_en.home", "extra_en"]
    assert rows["protists"]["gaps"] == 0


def test_name_en_empty_is_counted_separately_not_as_a_gap(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    ds.files["bacteria"][0]["name_en"] = ""
    rows, gaps = rows_by_group(ds)
    assert rows["bacteria"]["name_en_empty"] == 1 and rows["bacteria"]["gaps"] == 0 and gaps == {}


def test_coverage_command_writes_report(tmp_path, capsys):
    ds = Dataset(str(tmp_path / "data"))
    ds.files["bacteria"][0]["summary_en"] = ""
    ds.write()
    out = str(tmp_path / "reports" / "coverage.md")
    args = ms.build_parser().parse_args(["coverage", "--data", ds.root, "--out", out])
    assert ms.cmd_coverage(args) == 0
    text = open(out, encoding="utf-8").read()
    assert "| bacteria | 1 | 1 |" in text and "| protists | 1 | 0 |" in text and "escherichia-coli" in text
    assert "รวมช่องอังกฤษที่ยังว่าง: 1" in capsys.readouterr().out


# ---------------------------------------------------------------- เนื้อหา 8 ส่วน

def full_org(o):
    o["authority"] = "Escherich, 1885"
    o["traits"] = {"shape": "rod"}
    o["traits_text_th"] = {"food": "a", "home": "b", "x": "c"}
    o["traits_text_en"] = {"food": "a", "home": "b"}
    o["refs"] = [{"title": "a", "url": "https://x.org/1", "accessed": "2026-11-14"}, {"title": "b", "url": "https://x.org/2", "accessed": "2026-11-14"}]
    o["extra_th"] = {"lede": "x", "traitsExtra": [["a", "b"], ["c", "d"], ["e", "f"]], "life": [["a", "b"]], "lifecycle": [["a", "b"]],
                     "why": [["a", "b"]], "name": [["a", "b"]], "aside": ["x"]}
    return o


def test_empty_organism_has_none_of_the_sections():
    o = {"traits": {}, "traits_text_th": {}, "traits_text_en": {}}
    assert not any(ms.organism_sections(o, "th").values()) and not any(ms.organism_sections(o, "en").values())


def test_full_organism_has_all_sections_in_thai_and_title_refs_are_shared():
    o = full_org({})
    assert all(ms.organism_sections(o, "th").values())
    en = ms.organism_sections(o, "en")   # ยังไม่มี extra_en: ส่วนข้อความว่าง ส่วนที่ไม่ขึ้นกับภาษาครบ
    assert en["title"] and en["refs"] and not en["lede"] and not en["life"] and not en["name"]


def test_sections_have_thresholds():
    o = full_org({})
    o["refs"] = o["refs"][:1]
    o["extra_th"]["aside"] = []
    o["extra_th"]["traitsExtra"] = [["a", "b"]]
    got = ms.organism_sections(o, "th")
    assert not got["refs"] and not got["name"] and not got["traits"]   # 1 อ้างอิง, ไม่มีเกร็ด, แถวลักษณะ 1+2+1 = 4 < 6
    o["extra_th"]["lede"] = "  "
    assert not ms.organism_sections(o, "th")["lede"]


def test_content_coverage_counts_per_group_and_language(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    full_org(ds.files["bacteria"][0])
    ds.write()
    rows, per_org = ms.content_coverage_data(ds.root)
    r = {x["id"]: x for x in rows}
    assert r["bacteria"]["th"]["life"] == 1 and r["bacteria"]["en"]["life"] == 0 and r["bacteria"]["en"]["refs"] == 1
    assert r["protists"]["th"]["life"] == 0 and r["protists"]["species"] == 1
    assert [x["id"] for x in per_org] == ["escherichia-coli", "plasmodium-falciparum"]


def test_coverage_command_also_writes_content_report_next_to_it(tmp_path, capsys):
    ds = Dataset(str(tmp_path / "data"))
    full_org(ds.files["bacteria"][0])
    ds.write()
    out = str(tmp_path / "reports" / "coverage.md")
    args = ms.build_parser().parse_args(["coverage", "--data", ds.root, "--out", out])
    assert ms.cmd_coverage(args) == 0
    text = open(str(tmp_path / "reports" / "content-coverage.md"), encoding="utf-8").read()
    assert "ภาษาไทย" in text and "ภาษาอังกฤษ" in text and "| `escherichia-coli` | ✓ |" in text and "| `plasmodium-falciparum` | – |" in text
    assert "เนื้อหา 8 ส่วน (th)" in capsys.readouterr().out
