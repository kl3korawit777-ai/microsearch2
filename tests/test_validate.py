"""ทดสอบ validate และ import-seed ด้วยข้อมูลจำลองเล็กๆ (ไม่พึ่งข้อมูลจริงใน data/)

แต่ละกรณีเริ่มจากชุดข้อมูลที่ถูกต้อง แก้ให้เสียทีละแบบ แล้วยืนยันว่า validate จับได้ด้วยรหัสที่คาดไว้
"""

import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import microsearch as ms  # noqa: E402


def make_groups():
    return {
        "groups": [
            {
                "id": "bacteria", "th": "แบคทีเรีย", "en": "Bacteria",
                "ranks": [{"th": "โดเมน", "en": "Domain"}, {"th": "ไฟลัม", "en": "Phylum"},
                          {"th": "วงศ์", "en": "Family"}, {"th": "สกุล", "en": "Genus"}],
                "traits": [{"key": "shape", "th": "รูปร่าง", "en": "Shape"},
                           {"key": "food", "th": "อาหาร", "en": "Food"}],
            },
            {
                "id": "protists", "th": "โพรทิสต์", "en": "Protists",
                "ranks": [{"th": "โดเมน", "en": "Domain"}, {"th": "ซูเปอร์กรุ๊ป", "en": "Supergroup"},
                          {"th": "เคลดใหญ่", "en": "Major clade"}, {"th": "สกุล", "en": "Genus"}],
                "traits": [{"key": "shape", "th": "รูปร่าง", "en": "Shape"}],
            },
        ],
        "trait_values": {"shape": {"rod": {"th": "ท่อน", "en": "Rod"}, "coccus": {"th": "กลม", "en": "Coccus"}}},
        "tags": [{"key": "science", "th": "วิทยาศาสตร์", "en": "Research"},
                 {"key": "medicine", "th": "การแพทย์", "en": "Medicine"}],
        "levels": {"hs": {"th": "ม.ปลาย", "en": "High school"}, "uni": {"th": "มหาวิทยาลัย", "en": "University"}},
    }


def make_taxa():
    def t(rank, about=True):
        return {"rank": rank, "reading_th": "อ่าน", "common_th": "",
                "about_th": "คำอธิบาย" if about else "", "about_en": "About" if about else "", "review": "ai_draft"}
    return {
        "Bacteria": t("domain"), "Proteobacteria": t("phylum"), "Enterobacteriaceae": t("family"),
        "Escherichia": t("genus", about=False),  # สกุลไม่ต้องมี about
        "Eukarya": t("domain"), "SAR": t("supergroup"), "Alveolata": t("major_clade"), "Plasmodium": t("genus", about=False),
    }


def make_bacteria():
    return {
        "id": "escherichia-coli", "group": "bacteria", "scientific_name": "Escherichia coli",
        "name_th": "อีโคไล", "name_en": "E. coli", "reading_th": "เอสเชอริเชีย โคไล",
        "lineage": [{"rank": "domain", "name": "Bacteria"}, {"rank": "phylum", "name": "Proteobacteria"},
                    {"rank": "family", "name": "Enterobacteriaceae"}, {"rank": "genus", "name": "Escherichia"}],
        "level": "hs", "tags": ["science"], "summary_th": "สรุป", "summary_en": "Summary",
        "traits": {"shape": "rod"}, "traits_text_th": {"food": "อาหาร"}, "traits_text_en": {"food": "Food"},
        "illustration": "rod",
        "images": [{"url": "https://example.org/a.jpg", "author": "ผู้ถ่าย", "license": "CC BY 4.0",
                    "source_url": "https://commons.wikimedia.org/wiki/File:A.jpg"}],
        "review": "ai_draft", "taxon_ids": {"gbif": None, "ncbi": None},
    }


def make_protist():
    return {
        "id": "plasmodium-falciparum", "group": "protists", "scientific_name": "Plasmodium falciparum",
        "name_th": "พลาสโมเดียม", "name_en": "Plasmodium", "reading_th": "พลาสโมเดียม ฟัลซิปารัม",
        "lineage": [{"rank": "domain", "name": "Eukarya"}, {"rank": "supergroup", "name": "SAR"},
                    {"rank": "major_clade", "name": "Alveolata"}, {"rank": "genus", "name": "Plasmodium"}],
        "level": "uni", "tags": ["medicine"], "summary_th": "สรุป", "summary_en": "Summary",
        "traits": {"shape": "coccus"}, "traits_text_th": {}, "traits_text_en": {},
        "images": [], "review": "ai_reviewed", "taxon_ids": {"gbif": 1, "ncbi": "5833"},
    }


class Dataset:
    """โฟลเดอร์ data จำลอง แก้ทีละส่วนแล้วเรียก check()"""

    def __init__(self, root):
        self.root = root
        self.groups = make_groups()
        self.taxa = make_taxa()
        self.files = {"bacteria": [make_bacteria()], "protists": [make_protist()]}

    def write(self):
        os.makedirs(os.path.join(self.root, "organisms"), exist_ok=True)
        for name, doc in (("groups.json", self.groups), ("taxa.json", self.taxa)):
            with open(os.path.join(self.root, name), "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)
        for stem, items in self.files.items():
            with open(os.path.join(self.root, "organisms", stem + ".json"), "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)

    def check(self):
        self.write()
        return ms.validate_data(self.root)


@pytest.fixture
def ds(tmp_path):
    return Dataset(str(tmp_path / "data"))


def error_codes(rep):
    return rep.codes("errors")


# ---------------------------------------------------------------- ข้อมูลดี

def test_valid_dataset_has_no_errors(ds):
    rep = ds.check()
    assert rep.errors == []


def test_unknown_family_marker_is_accepted(ds):
    ds.files["bacteria"][0]["lineage"][2]["name"] = "?"
    assert ds.check().errors == []


def test_genus_may_have_empty_about(ds):
    assert ds.taxa["Escherichia"]["about_th"] == ""
    assert ds.check().errors == []


def test_multiword_rank_name_is_normalised(ds):
    # "Major clade" ใน groups.json ต้องตรงกับ major_clade ใน lineage
    assert ds.check().errors == []


# ---------------------------------------------------------------- ข้อมูลเสีย (error)

def test_duplicate_id(ds):
    ds.files["bacteria"].append(copy.deepcopy(ds.files["bacteria"][0]))
    assert "DUP_ID" in error_codes(ds.check())


def test_duplicate_id_across_files(ds):
    dup = make_protist()
    dup["id"] = "escherichia-coli"
    dup["scientific_name"] = "Escherichia coli"
    ds.files["protists"].append(dup)
    assert "DUP_ID" in error_codes(ds.check())


def test_id_does_not_match_scientific_name(ds):
    ds.files["bacteria"][0]["id"] = "e-coli"
    assert "ID_MISMATCH" in error_codes(ds.check())


def test_id_with_invalid_characters(ds):
    ds.files["bacteria"][0]["id"] = "Escherichia_coli"
    codes = error_codes(ds.check())
    assert "SCHEMA" in codes and "ID_MISMATCH" in codes


def test_trait_value_not_allowed(ds):
    ds.files["bacteria"][0]["traits"]["shape"] = "cube"
    assert "TRAIT_VALUE" in error_codes(ds.check())


def test_trait_key_not_in_trait_values(ds):
    ds.files["bacteria"][0]["traits"]["color"] = "red"
    # food เป็นลักษณะของกลุ่มแต่ไม่มีใน trait_values ก็ต้องจับ
    ds.files["bacteria"][0]["traits"]["food"] = "x"
    rep = ds.check()
    assert "TRAIT_KEY" in error_codes(rep)
    assert len([e for e in rep.errors if e["code"] == "TRAIT_KEY"]) == 2


def test_lineage_missing_rank(ds):
    del ds.files["bacteria"][0]["lineage"][1]  # ตัด phylum
    rep = ds.check()
    assert "LINEAGE_RANKS" in error_codes(rep)
    assert "phylum" in next(e["msg"] for e in rep.errors if e["code"] == "LINEAGE_RANKS")


def test_lineage_extra_rank(ds):
    ds.files["bacteria"][0]["lineage"].insert(2, {"rank": "class", "name": "Proteobacteria"})
    assert "LINEAGE_RANKS" in error_codes(ds.check())


def test_lineage_rank_order_swapped(ds):
    lin = ds.files["bacteria"][0]["lineage"]
    lin[1], lin[2] = lin[2], lin[1]
    assert "LINEAGE_RANKS" in error_codes(ds.check())


def test_lineage_name_not_in_taxa(ds):
    ds.files["bacteria"][0]["lineage"][1]["name"] = "Nonexistentbacteria"
    assert "LINEAGE_NAME_NOT_IN_TAXA" in error_codes(ds.check())


def test_unknown_marker_only_allowed_at_family(ds):
    ds.files["bacteria"][0]["lineage"][1]["name"] = "?"
    assert "LINEAGE_UNKNOWN_RANK" in error_codes(ds.check())


def test_non_genus_taxon_without_about_th(ds):
    ds.taxa["Proteobacteria"]["about_th"] = ""
    rep = ds.check()
    assert "TAXON_ABOUT_MISSING" in error_codes(rep)
    assert any(e["id"] == "Proteobacteria" and "about_th" in e["msg"] for e in rep.errors)


def test_non_genus_taxon_without_about_en(ds):
    ds.taxa["Enterobacteriaceae"]["about_en"] = "   "
    assert "TAXON_ABOUT_MISSING" in error_codes(ds.check())


def test_taxon_with_null_rank_may_have_empty_about(ds):
    # ชื่อใหม่ของไฟลัม (rank null) ใช้แสดงคู่กับชื่อตำรา ไม่ต้องมี about
    ds.taxa["Pseudomonadota"] = {"rank": None, "reading_th": "x", "common_th": "", "about_th": "", "about_en": "",
                                 "review": "ai_draft"}
    assert ds.check().errors == []


def test_taxon_with_empty_string_rank_still_needs_about(ds):
    ds.taxa["Pseudomonadota"] = {"rank": "", "reading_th": "x", "common_th": "", "about_th": "", "about_en": "",
                                 "review": "ai_draft"}
    assert "TAXON_ABOUT_MISSING" in error_codes(ds.check())


def test_taxon_schema_bad_review(ds):
    ds.taxa["Bacteria"]["review"] = "draft"
    assert "SCHEMA" in error_codes(ds.check())


def test_missing_reading_th(ds):
    ds.files["bacteria"][0]["reading_th"] = ""
    assert "READING_MISSING" in error_codes(ds.check())


def test_reading_th_field_absent(ds):
    del ds.files["bacteria"][0]["reading_th"]
    assert "SCHEMA" in error_codes(ds.check())


def test_bad_level(ds):
    ds.files["bacteria"][0]["level"] = "college"
    assert "SCHEMA" in error_codes(ds.check())


def test_bad_tag(ds):
    ds.files["bacteria"][0]["tags"] = ["science", "cooking"]
    assert "TAG_UNKNOWN" in error_codes(ds.check())


@pytest.mark.parametrize("bad", ["draft", "approved", ""])
def test_bad_review_value(ds, bad):
    ds.files["bacteria"][0]["review"] = bad
    assert "SCHEMA" in error_codes(ds.check())


@pytest.mark.parametrize("review", ["ai_draft", "ai_reviewed", "human_reviewed"])
def test_good_review_values(ds, review):
    ds.files["bacteria"][0]["review"] = review
    assert ds.check().errors == []


@pytest.mark.parametrize("field", ["url", "author", "license", "source_url"])
def test_image_missing_required_field(ds, field):
    del ds.files["bacteria"][0]["images"][0][field]
    rep = ds.check()
    assert "SCHEMA" in error_codes(rep)
    assert any(field in e["msg"] for e in rep.errors)


def test_image_with_empty_license(ds):
    ds.files["bacteria"][0]["images"][0]["license"] = ""
    assert "SCHEMA" in error_codes(ds.check())


def test_unknown_group(ds):
    ds.files["bacteria"][0]["group"] = "viruses"
    assert "GROUP_UNKNOWN" in error_codes(ds.check())


def test_group_does_not_match_file(ds):
    ds.files["bacteria"][0]["group"] = "protists"
    assert "GROUP_FILE_MISMATCH" in error_codes(ds.check())


def test_missing_required_field(ds):
    del ds.files["bacteria"][0]["summary_th"]
    assert "SCHEMA" in error_codes(ds.check())


def test_wrong_type(ds):
    ds.files["bacteria"][0]["tags"] = "science"
    assert "SCHEMA" in error_codes(ds.check())


def test_unknown_field_is_rejected(ds):
    ds.files["bacteria"][0]["colour"] = "red"
    assert "SCHEMA" in error_codes(ds.check())


def test_invalid_json_file(ds):
    ds.write()
    with open(os.path.join(ds.root, "organisms", "bacteria.json"), "w", encoding="utf-8") as f:
        f.write("[{ไม่ใช่ json")
    assert "JSON_INVALID" in error_codes(ms.validate_data(ds.root))


def test_missing_taxa_file(ds):
    ds.write()
    os.remove(os.path.join(ds.root, "taxa.json"))
    assert "FILE_MISSING" in error_codes(ms.validate_data(ds.root))


def test_missing_groups_file(ds):
    ds.write()
    os.remove(os.path.join(ds.root, "groups.json"))
    assert "FILE_MISSING" in error_codes(ms.validate_data(ds.root))


def test_error_names_file_and_id(ds):
    ds.files["bacteria"][0]["traits"]["shape"] = "cube"
    err = next(e for e in ds.check().errors if e["code"] == "TRAIT_VALUE")
    assert err["file"] == "organisms/bacteria.json" and err["id"] == "escherichia-coli"


# ---------------------------------------------------------------- warning

def test_empty_english_fields_are_warnings_not_errors(ds):
    o = ds.files["bacteria"][0]
    o["name_en"] = ""
    o["summary_en"] = ""
    o["traits_text_en"] = {}
    rep = ds.check()
    assert rep.errors == []
    assert {"EN_EMPTY_NAME_EN", "EN_EMPTY_SUMMARY_EN", "EN_EMPTY_TRAITS_TEXT_EN"} <= rep.codes("warnings")


def test_extra_th_without_extra_en_is_warning(ds):
    ds.files["bacteria"][0]["extra_th"] = {"lede": "x"}
    rep = ds.check()
    assert rep.errors == []
    assert "EN_EMPTY_EXTRA_EN" in rep.codes("warnings")


def test_valid_dataset_has_no_warnings(ds):
    assert ds.check().warnings == []


# ---------------------------------------------------------------- คำสั่ง validate (CLI)

def test_cli_exit_code_and_thai_output(ds, capsys):
    ds.write()
    assert ms.main(["validate", "--data", ds.root]) == 0
    assert "ผ่าน" in capsys.readouterr().out
    ds.files["bacteria"][0]["traits"]["shape"] = "cube"
    ds.write()
    assert ms.main(["validate", "--data", ds.root]) == 1
    out = capsys.readouterr().out
    assert "ข้อผิดพลาด" in out and "escherichia-coli" in out and "organisms/bacteria.json" in out


# ---------------------------------------------------------------- import-seed

@pytest.fixture
def seed_and_data(tmp_path):
    seed = Dataset(str(tmp_path / "seed"))
    seed.write()
    return str(tmp_path / "seed"), str(tmp_path / "data")


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def run_import(seed, data, *extra):
    return ms.main(["import-seed", "--seed", seed, "--data", data, *extra])


def test_import_seed_copies_byte_for_byte(seed_and_data):
    seed, data = seed_and_data
    assert run_import(seed, data) == 0
    for rel in ("taxa.json", "groups.json", "organisms/bacteria.json", "organisms/protists.json"):
        assert read_bytes(os.path.join(seed, rel)) == read_bytes(os.path.join(data, rel))
    assert ms.validate_data(data).errors == []


def test_import_seed_twice_is_idempotent(seed_and_data, capsys):
    seed, data = seed_and_data
    run_import(seed, data)
    capsys.readouterr()
    assert run_import(seed, data) == 0
    assert "คัดลอก 0" in capsys.readouterr().out


def test_import_seed_does_not_overwrite_edited_file(seed_and_data):
    seed, data = seed_and_data
    run_import(seed, data)
    edited = os.path.join(data, "organisms", "bacteria.json")
    with open(edited, "w", encoding="utf-8") as f:
        f.write('["แก้แล้ว"]')
    assert run_import(seed, data) == 0  # ไม่มี tty / ไม่ตอบ y -> ข้าม
    assert read_bytes(edited) == '["แก้แล้ว"]'.encode("utf-8")


def test_import_seed_force_overwrites(seed_and_data):
    seed, data = seed_and_data
    run_import(seed, data)
    edited = os.path.join(data, "organisms", "bacteria.json")
    with open(edited, "w", encoding="utf-8") as f:
        f.write("[]")
    assert run_import(seed, data, "--force") == 0
    assert read_bytes(edited) == read_bytes(os.path.join(seed, "organisms", "bacteria.json"))


def test_import_seed_asks_before_overwrite(seed_and_data):
    seed, data = seed_and_data
    run_import(seed, data)
    edited = os.path.join(data, "taxa.json")
    with open(edited, "w", encoding="utf-8") as f:
        f.write("{}")
    args = ms.build_parser().parse_args(["import-seed", "--seed", seed, "--data", data])
    asked = []
    assert ms.cmd_import_seed(args, ask=lambda rel: asked.append(rel) or False) == 0
    assert asked == ["taxa.json"] and read_bytes(edited) == b"{}"
    assert ms.cmd_import_seed(args, ask=lambda rel: True) == 0
    assert read_bytes(edited) == read_bytes(os.path.join(seed, "taxa.json"))


def test_import_seed_never_changes_seed(seed_and_data):
    seed, data = seed_and_data
    before = {rel: read_bytes(os.path.join(seed, rel)) for rel in ms.seed_files(seed)}
    run_import(seed, data, "--force")
    assert before == {rel: read_bytes(os.path.join(seed, rel)) for rel in ms.seed_files(seed)}


def test_import_seed_missing_seed_dir(tmp_path):
    assert run_import(str(tmp_path / "nope"), str(tmp_path / "data")) == 1
