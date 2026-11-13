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
