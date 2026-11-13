"""iNaturalist และ GBIF เป็นแหล่งเสริมของรูป: กรอง license, ผู้ถ่าย, ชนิดที่ตรง, ไม่ซ้ำ, ไม่เกินจำนวนที่กำหนด
ใช้ API จำลอง ไม่ยิงเน็ตจริง"""

import io
import json
import os
import sys
import urllib.parse

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
sys.path.insert(0, HERE)
import microsearch as ms  # noqa: E402
from test_images import checked, good_image, orgs, run_check, webp_bytes  # noqa: E402,F401
from test_validate import Dataset  # noqa: E402


@pytest.mark.parametrize("url,want", [
    ("https://creativecommons.org/publicdomain/zero/1.0/", "CC0"), ("https://creativecommons.org/licenses/by/4.0/", "CC BY 4.0"),
    ("http://creativecommons.org/licenses/by-sa/3.0", "CC BY-SA 3.0"), ("https://creativecommons.org/licenses/by-nc/4.0/", None),
    ("https://creativecommons.org/licenses/by-nd/4.0/", None), ("https://creativecommons.org/licenses/by-nc-sa/4.0/", None),
    ("", None), (None, None), ("All rights reserved", None),
])
def test_gbif_license(url, want):
    assert ms.gbif_license(url) == want


def test_inat_author_parsing():
    assert ms.inat_author({"attribution": "(c) Jane Doe, some rights reserved (CC BY)"}, {"login": "jd"}) == "Jane Doe"
    assert ms.inat_author({"attribution": "no rights reserved"}, {"login": "jd", "name": "J D"}) == "J D"
    assert ms.inat_author({}, {"login": "jd"}) == "jd"


def inat_json(sci, photos, taxon=None, uri="https://www.inaturalist.org/observations/1"):
    return json.dumps({"results": [{"id": 1, "uri": uri, "description": "", "user": {"login": "u"},
                                    "taxon": {"name": taxon or sci}, "photos": photos}]})


def photo(pid, code="cc-by", hidden=False):
    return {"id": pid, "license_code": code, "hidden": hidden, "attribution": "(c) Jane, some rights reserved (CC BY)",
            "url": "https://inaturalist-open-data.s3.amazonaws.com/photos/%d/square.jpeg" % pid, "original_dimensions": {"width": 2000, "height": 1500}}


def gbif_json(sci, media, **occ):
    base = {"key": 77, "scientificName": sci, "taxonRank": "SPECIES", "license": "http://creativecommons.org/licenses/by/4.0/", "media": media}
    base.update(occ)
    return json.dumps({"results": [base]})


def medium(ident, lic="http://creativecommons.org/licenses/by/4.0/", creator="Pat"):
    return {"type": "StillImage", "identifier": ident, "license": lic, "creator": creator}


class FakeOpen:
    def __init__(self):
        self.inat, self.gbif, self.calls, self.byte_calls = {}, {}, [], []

    def __call__(self, url):
        self.calls.append(url)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if "api.inaturalist.org" in url:
            return self.inat.get(q["taxon_name"][0], json.dumps({"results": []}))
        return self.gbif.get(q["scientificName"][0], json.dumps({"results": []}))

    def get_bytes(self, url):
        self.byte_calls.append(url)
        from PIL import Image
        buf = io.BytesIO()
        size = (300, 200) if "tiny" in url else (1800, 1200)
        Image.effect_noise(size, 60).convert("RGB").save(buf, "JPEG", quality=95)
        return buf.getvalue()


def test_inat_candidates_filter_license_hidden_and_other_taxa(tmp_path):
    api = FakeOpen()
    api.inat["Foo bar"] = inat_json("Foo bar", [photo(1), photo(2, "cc-by-sa"), photo(3, "cc0"), photo(4, "cc-by-nc"), photo(5, hidden=True), photo(6, "")])
    fx = ms.Fetcher(str(tmp_path / "c"), getter=api, intervals={})
    got = ms.inat_candidates(fx, "Foo bar")
    assert [c["photo_id"] for c in got] == ["1", "2", "3"]
    assert [c["license_raw"] for c in got] == ["CC BY 4.0", "CC BY-SA 4.0", "CC0"]
    assert got[0]["thumb"].endswith("/photos/1/large.jpeg") and got[0]["page"] == "https://www.inaturalist.org/observations/1" and got[0]["author"] == "Jane"
    api.inat["Foo baz"] = inat_json("Foo baz", [photo(9)], taxon="Foo baz var. x")
    assert ms.inat_candidates(fx, "Foo baz") == []


def test_inat_page_url_is_https(tmp_path):
    api = FakeOpen()
    api.inat["Foo bar"] = inat_json("Foo bar", [photo(1)], uri="http://www.inaturalist.org/observations/9")
    fx = ms.Fetcher(str(tmp_path / "c"), getter=api, intervals={})
    assert ms.inat_candidates(fx, "Foo bar")[0]["page"] == "https://www.inaturalist.org/observations/9"


def test_gbif_candidates_require_open_license_author_and_matching_species(tmp_path):
    api = FakeOpen()
    api.gbif["Foo bar"] = gbif_json("Foo bar", [medium("https://x/a.jpg"), medium("https://x/b.jpg", lic="http://creativecommons.org/licenses/by-nc/4.0/"),
                                                medium("https://x/c.jpg", creator=""), {"type": "Sound", "identifier": "https://x/d.mp3"}])
    fx = ms.Fetcher(str(tmp_path / "c"), getter=api, intervals={})
    got = ms.gbif_candidates(fx, "Foo bar")
    assert [c["thumb"] for c in got] == ["https://x/a.jpg"] and got[0]["page"] == "https://www.gbif.org/occurrence/77"
    api.gbif["Foo baz"] = gbif_json("Other species", [medium("https://x/e.jpg")])
    assert ms.gbif_candidates(fx, "Foo baz") == []


@pytest.fixture
def open_world(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    ds.files["bacteria"][0]["images"] = [dict(good_image(), title="File:Existing.jpg", original_url="https://upload.wikimedia.org/x/1.jpg")]
    ds.write()
    (tmp_path / "site" / "images" / "escherichia-coli").mkdir(parents=True)
    (tmp_path / "site" / "images" / "escherichia-coli" / "1.webp").write_bytes(webp_bytes())
    api = FakeOpen()
    fx = ms.Fetcher(str(tmp_path / "cache"), getter=api, bytes_getter=api.get_bytes, intervals={})
    return ds, api, fx, tmp_path


def run_supplement(ds, fx, tmp, *extra):
    args = ms.build_parser().parse_args(["images", "--supplement", "inaturalist,gbif", "--data", ds.root, "--cache", str(tmp / "cache"),
                                         "--images-dir", str(tmp / "site" / "images"), "--missing-report", str(tmp / "reports" / "images-missing.md"), *extra])
    return ms.cmd_images(args, fetcher=fx)


def test_supplement_adds_pictures_from_both_sources_and_keeps_existing(open_world):
    pytest.importorskip("PIL")
    ds, api, fx, tmp = open_world
    api.inat["Escherichia coli"] = inat_json("Escherichia coli", [photo(11), photo(12, "cc-by-sa")])
    api.gbif["Escherichia coli"] = gbif_json("Escherichia coli", [medium("https://host/gbif1.jpg"), medium("https://host/gbif2.jpg")])
    assert run_supplement(ds, fx, tmp, "--per-species", "3") == 0
    imgs = orgs(ds)["escherichia-coli"]["images"]
    assert len(imgs) == 3 and imgs[0]["title"] == "File:Existing.jpg"   # รูปเดิมอยู่หน้าสุดและไม่ถูกแตะ
    assert {i.get("source", "commons") for i in imgs[1:]} <= {"inaturalist", "gbif"}
    for i in imgs[1:]:
        assert i["author"] and ms.ALLOWED_LICENSE_RE.match(i["license"]) and i["source_url"].startswith(ms.IMAGE_SOURCE_HOSTS)
        assert (tmp / "site" / i["url"]).exists() and (tmp / "site" / i["url_small"]).exists()
    assert ms.validate_data(ds.root).errors == []


def test_supplement_respects_the_cap_and_is_idempotent(open_world):
    pytest.importorskip("PIL")
    ds, api, fx, tmp = open_world
    api.inat["Escherichia coli"] = inat_json("Escherichia coli", [photo(11), photo(12), photo(13), photo(14)])
    run_supplement(ds, fx, tmp, "--per-species", "2")
    assert len(orgs(ds)["escherichia-coli"]["images"]) == 2
    calls = len(api.calls) + len(api.byte_calls)
    run_supplement(ds, fx, tmp, "--per-species", "2")
    assert len(orgs(ds)["escherichia-coli"]["images"]) == 2 and len(api.calls) + len(api.byte_calls) == calls


def test_supplement_fills_species_with_no_picture_and_updates_missing_report(open_world):
    pytest.importorskip("PIL")
    ds, api, fx, tmp = open_world
    api.inat["Plasmodium falciparum"] = inat_json("Plasmodium falciparum", [photo(21)])
    run_supplement(ds, fx, tmp)
    assert len(orgs(ds)["plasmodium-falciparum"]["images"]) == 1
    report = (tmp / "reports" / "images-missing.md").read_text(encoding="utf-8")
    assert "plasmodium-falciparum" not in report and "ไม่มีรูป 0 ชนิด" in report


def test_supplement_dedupes_the_same_inat_photo_seen_through_gbif(open_world):
    pytest.importorskip("PIL")
    ds, api, fx, tmp = open_world
    api.inat["Escherichia coli"] = inat_json("Escherichia coli", [photo(31)])
    api.gbif["Escherichia coli"] = gbif_json("Escherichia coli", [medium("https://inaturalist-open-data.s3.amazonaws.com/photos/31/original.jpg")])
    run_supplement(ds, fx, tmp, "--per-species", "3")
    assert len(orgs(ds)["escherichia-coli"]["images"]) == 2


def test_supplement_rejects_pictures_that_turn_out_too_small(open_world):
    pytest.importorskip("PIL")
    ds, api, fx, tmp = open_world
    api.gbif["Escherichia coli"] = gbif_json("Escherichia coli", [medium("https://host/tiny.jpg")])
    run_supplement(ds, fx, tmp)
    assert len(orgs(ds)["escherichia-coli"]["images"]) == 1 and not (tmp / "site" / "images" / "escherichia-coli" / "2.webp").exists()


def test_supplement_unknown_source_is_refused(open_world, capsys):
    ds, api, fx, tmp = open_world
    args = ms.build_parser().parse_args(["images", "--supplement", "flickr", "--data", ds.root])
    assert ms.cmd_images(args, fetcher=fx) == 1 and "flickr" in capsys.readouterr().out


def test_check_accepts_inaturalist_and_gbif_sources_but_not_others(checked, capsys):
    ds, tmp = checked
    img = ds.files["bacteria"][0]["images"][0]
    img["source_url"] = "https://www.inaturalist.org/observations/1"
    ds.write()
    assert run_check(ds, tmp, capsys)[0] == 0
    img["source_url"] = "https://www.gbif.org/occurrence/77"
    ds.write()
    assert run_check(ds, tmp, capsys)[0] == 0
    img["source_url"] = "https://www.flickr.com/photos/x/1"
    ds.write()
    rc, out = run_check(ds, tmp, capsys)
    assert rc == 1 and "iNaturalist" in out
