"""ทดสอบ export-translation / import-translation (R9): ต้นฉบับแปลต้องตรงกับ extra_th ทั้งโครงสร้าง เลข [n] และตัวเลข ไม่มีอักษรไทยหลุด"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, HERE)
import microsearch as ms  # noqa: E402
from test_validate import Dataset, ds  # noqa: E402,F401

TH = {
    "lede": "แบคทีเรียรูปท่อน ยาว 2 ไมโครเมตร [1] พบในลำไส้ [2]",
    "traitsExtra": [["จีโนม", "4.64 ล้านคู่เบส มี 4,288 ยีน [1]"]],
    "life": [["แหล่งที่อยู่", "ลำไส้ใหญ่ [2]"]],
    "name": [["Escherichia", "ตั้งตามเอเชอริช [2]"]],
    "asideTitle": "ชื่อทดสอบ",
    "aside": ["ชื่อเดิม Bacterium coli [2]", "ยอมรับปี 1958 [1]"],
    "disease": {"name": "ท้องเสีย [1]", "symptoms": "ถ่ายเหลว [2]"},
    "warning": {"text": "ห้ามกิน [1]", "myths": ["ความเชื่อ [2]"]},
    "refs": [{"title": "A", "url": "https://example.org/a", "accessed": "2026-11-14"},
             {"title": "B", "url": "https://example.org/b", "accessed": "2026-11-14"}],
}

EN_OK = """## escherichia-coli
lede: A rod-shaped bacterium, 2 micrometers long [1], found in the gut [2]
traitsExtra: Genome | 4.64 million base pairs, 4,288 genes [1]
life: Habitat | Large intestine [2]
name: Escherichia | Named after Escherich [2]
asideTitle: A test name
aside: Formerly Bacterium coli [2]
aside: Accepted in 1958 [1]
disease.name: Diarrhea [1]
disease.symptoms: Loose stools [2]
warning.text: Do not eat [1]
warning.myths: A belief [2]
"""


@pytest.fixture
def world(tmp_path):
    d = Dataset(str(tmp_path / "data"))
    d.write()
    path = os.path.join(d.root, "organisms", "bacteria.json")
    items = json.load(open(path, encoding="utf-8"))
    extra = json.loads(json.dumps(TH))
    items[0]["refs"] = extra.pop("refs")
    items[0]["tags"] = ["science", "medicine"]
    items[0]["extra_th"] = extra
    items[0].pop("extra_en", None)
    json.dump(items, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    return d, tmp_path


def run_import(world, text, *extra):
    d, tmp = world
    src = tmp / "en.txt"
    src.write_text(text, encoding="utf-8")
    args = ms.build_parser().parse_args(["import-translation", str(src), "--data", d.root, *extra])
    return ms.cmd_import_translation(args)


def org(world):
    d, _ = world
    return json.load(open(os.path.join(d.root, "organisms", "bacteria.json"), encoding="utf-8"))[0]


def test_lines_round_trip():
    lines = ms.extra_to_lines(TH)
    ex, errs = ms.lines_to_extra(lines)
    assert not errs
    assert ms.extra_to_lines(ex) == lines


def test_export_writes_one_block_per_species(world, tmp_path):
    d, tmp = world
    out = tmp / "th.txt"
    args = ms.build_parser().parse_args(["export-translation", "bacteria", "--out", str(out), "--data", d.root])
    assert ms.cmd_export_translation(args) == 0
    text = out.read_text(encoding="utf-8")
    assert text.startswith("## escherichia-coli\n")
    assert "traitsExtra: จีโนม | 4.64" in text and "warning.myths: ความเชื่อ [2]" in text


def test_dry_run_changes_nothing(world):
    assert run_import(world, EN_OK, "--dry-run") == 0
    assert "extra_en" not in org(world)


def test_import_writes_extra_en_and_validate_passes(world):
    assert run_import(world, EN_OK) == 0
    en = org(world)["extra_en"]
    assert en["lede"].startswith("A rod-shaped") and en["aside"][1] == "Accepted in 1958 [1]"
    assert en["traitsExtra"] == [["Genome", "4.64 million base pairs, 4,288 genes [1]"]]
    assert en["disease"]["symptoms"] == "Loose stools [2]" and en["warning"]["myths"] == ["A belief [2]"]


@pytest.mark.parametrize("old,new,expect", [
    ("found in the gut [2]", "found in the gut [1]", "[n]"),
    ("2 micrometers", "3 micrometers", "ตัวเลข"),
    ("aside: Accepted in 1958 [1]\n", "", "จำนวนบรรทัด"),
    ("Large intestine [2]", "ลำไส้ [2]", "อักษรไทย"),
    ("4,288 genes", "4288 genes", None),  # ใส่คอมมาหรือไม่ก็ได้ ตัวเลขเท่ากัน
])
def test_mismatch_stops_without_writing(world, capsys, old, new, expect):
    rc = run_import(world, EN_OK.replace(old, new))
    if expect is None:
        assert rc == 0
        return
    assert rc == 1 and expect in capsys.readouterr().out
    assert "extra_en" not in org(world)


def test_unknown_key_and_missing_separator_are_reported(world, capsys):
    assert run_import(world, EN_OK.replace("life: Habitat | Large", "life: Habitat - Large")) == 1
    assert "ป้ายกับข้อความ" in capsys.readouterr().out
    assert run_import(world, EN_OK + "foo: bar\n") == 1
    assert "คีย์ไม่รู้จัก" in capsys.readouterr().out


def test_species_without_extra_th_is_rejected(world, capsys):
    assert run_import(world, EN_OK.replace("## escherichia-coli", "## nonexistent-species")) == 1
    assert "ไม่มีชนิดนี้" in capsys.readouterr().out


def test_real_data_all_species_have_matching_english():
    """ข้อมูลจริง: extra_en ทุกชนิดต้องตรงกับ extra_th ตามกฎเดียวกับตอนนำเข้า"""
    data = os.path.join(ROOT, "data")
    if not os.path.isdir(os.path.join(data, "organisms")):
        pytest.skip("ไม่มี data/organisms")
    bad = []
    for o in ms.load_organisms(data):
        if o.get("extra_th"):
            if not o.get("extra_en"):
                bad.append("%s: ไม่มี extra_en" % o["id"])
            else:
                bad += ms.compare_translation(o["id"], o["extra_th"], o["extra_en"])
    assert not bad, bad[:5]
