"""ทดสอบคำสั่ง build: ต้อง validate ก่อน, ไม่เขียนไฟล์เมื่อมี error, ผลลัพธ์ย่อขนาดและครบ"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
sys.path.insert(0, HERE)
import microsearch as ms  # noqa: E402
from test_validate import Dataset  # noqa: E402


@pytest.fixture
def world(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    ds.groups["groups"][0]["phyla"] = [{"name": "Proteobacteria", "new_name": "Pseudomonadota"}]
    ds.groups["groups"][1]["phyla"] = [{"name": "SAR", "new_name": ""}]
    ds.taxa["Proteobacteria"]["reading_th"] = "โพรทีโอแบคทีเรีย"
    ds.write()
    illus = tmp_path / "illustrations.json"
    illus.write_text(json.dumps({"rod": "<path/>"}), encoding="utf-8")
    return ds, str(illus), str(tmp_path / "out")


def run_build(ds, illus, out):
    args = ms.build_parser().parse_args(["build", "--data", ds.root, "--out", out, "--illustrations", illus])
    return ms.cmd_build(args)


def read(out, name):
    with open(os.path.join(out, name), encoding="utf-8") as f:
        return json.load(f)


def test_build_writes_expected_files(world):
    ds, illus, out = world
    assert run_build(ds, illus, out) == 0
    assert sorted(os.listdir(out)) == ["bacteria.json", "illustrations.json", "index.json", "meta.json", "protists.json"]
    index = read(out, "index.json")
    assert [r["id"] for r in index] == ["escherichia-coli", "plasmodium-falciparum"]
    assert read(out, "bacteria.json")["organisms"][0]["lineage"][1]["name"] == "Proteobacteria"


def test_build_output_is_minified(world):
    ds, illus, out = world
    run_build(ds, illus, out)
    for name in os.listdir(out):
        text = open(os.path.join(out, name), encoding="utf-8").read()
        again = json.dumps(json.loads(text), ensure_ascii=False, separators=(",", ":"))
        assert text == again + "\n", name  # ไม่มีช่องว่างเกิน ไม่ escape ภาษาไทย


def test_index_row_fields_and_search_haystack(world):
    ds, illus, out = world
    run_build(ds, illus, out)
    row = read(out, "index.json")[0]
    assert row["g"] == "bacteria" and row["p"] == 0 and row["sci"] == "Escherichia coli" and row["lv"] == "hs"
    assert row["q"] == row["q"].lower()
    for needle in ("escherichia coli", "proteobacteria", "pseudomonadota", "enterobacteriaceae", "โพรทีโอแบคทีเรีย", "research"):
        assert needle in row["q"], needle


def test_phylum_index_for_protist_supergroup(world):
    ds, illus, out = world
    run_build(ds, illus, out)
    assert read(out, "index.json")[1]["p"] == 0


def test_group_file_has_used_taxa_with_readings(world):
    ds, illus, out = world
    run_build(ds, illus, out)
    taxa = read(out, "bacteria.json")["taxa"]
    assert set(taxa) == {"Bacteria", "Proteobacteria", "Enterobacteriaceae", "Escherichia"}
    assert taxa["Proteobacteria"]["reading_th"] == "โพรทีโอแบคทีเรีย"


def test_meta_carries_phyla_readings(world):
    ds, illus, out = world
    run_build(ds, illus, out)
    readings = read(out, "meta.json")["readings"]
    assert readings["Proteobacteria"] == "โพรทีโอแบคทีเรีย" and "SAR" in readings and "Escherichia" not in readings


def test_build_is_deterministic(world):
    ds, illus, out = world
    run_build(ds, illus, out)
    first = {n: open(os.path.join(out, n), "rb").read() for n in os.listdir(out)}
    run_build(ds, illus, out)
    assert first == {n: open(os.path.join(out, n), "rb").read() for n in os.listdir(out)}


def test_build_removes_stale_json(world):
    ds, illus, out = world
    os.makedirs(out)
    with open(os.path.join(out, "old-group.json"), "w") as f:
        f.write("{}")
    run_build(ds, illus, out)
    assert "old-group.json" not in os.listdir(out)


def test_build_stops_on_validation_error_and_writes_nothing(world, capsys):
    ds, illus, out = world
    ds.files["bacteria"][0]["traits"]["shape"] = "cube"
    ds.write()
    os.makedirs(out)
    with open(os.path.join(out, "index.json"), "w") as f:
        f.write("SENTINEL")
    assert run_build(ds, illus, out) == 1
    assert os.listdir(out) == ["index.json"] and open(os.path.join(out, "index.json")).read() == "SENTINEL"
    assert "หยุด build" in capsys.readouterr().out


def test_build_does_not_create_output_dir_on_error(world):
    ds, illus, out = world
    ds.files["bacteria"][0]["id"] = "wrong"
    ds.write()
    assert run_build(ds, illus, out) == 1
    assert not os.path.exists(out)


def test_build_fails_when_phylum_is_unknown(world, capsys):
    ds, illus, out = world
    ds.groups["groups"][0]["phyla"] = [{"name": "Firmicutes", "new_name": ""}]
    ds.write()
    assert run_build(ds, illus, out) == 1
    assert "escherichia-coli" in capsys.readouterr().out and not os.path.exists(out)
