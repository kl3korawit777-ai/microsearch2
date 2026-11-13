"""ทดสอบคำสั่ง images (ค้น Wikimedia Commons, กรอง license, ให้คะแนน, ย่อเป็น WebP) และ images --check
ใช้ API จำลอง ไม่ยิงเน็ตจริง รูปจริงสร้างด้วย Pillow (ข้ามเทสต์ย่อรูปถ้าไม่มี Pillow)"""

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
from test_validate import Dataset  # noqa: E402


# ---------------------------------------------------------------- license

@pytest.mark.parametrize("raw,want", [
    ("CC0", "CC0"), ("CC0 1.0", "CC0"), ("CC BY 4.0", "CC BY 4.0"), ("CC BY-SA 3.0", "CC BY-SA 3.0"),
    ("CC BY 3.0 US", "CC BY 3.0 US"), ("cc-by-sa 2.5", "CC BY-SA 2.5"), ("CC BY-SA 4.0", "CC BY-SA 4.0"),
    ("Public domain", "Public domain"), ("PD-USGov-HHS-CDC", "Public domain"), ("PD-old-100", "Public domain"),
])
def test_accepted_licenses(raw, want):
    assert ms.normalize_license(raw) == want
    assert ms.ALLOWED_LICENSE_RE.match(want)


@pytest.mark.parametrize("raw", [
    "", None, "CC BY-NC 4.0", "CC BY-NC-SA 3.0", "CC BY-ND 2.0", "CC BY-SA-NC 3.0", "GFDL", "GFDL 1.2", "Attribution", "CC BY",
    "Copyrighted free use", "Fair use", "OGL 3.0", "All rights reserved", "Free Art License", "CC BY-SA", "Unknown",
])
def test_rejected_licenses(raw):
    assert ms.normalize_license(raw) is None


def test_strip_html():
    assert ms.strip_html('<a href="x">Jane &amp; Co</a>  <b>Doe</b>') == "Jane & Co Doe"


# ---------------------------------------------------------------- ผู้สมัครและคะแนน

def cand(title="File:X.jpg", lic="CC BY 4.0", author="A. Person", width=2000, mime="image/jpeg", desc="", cats="", thumb="https://t/x.jpg"):
    return {"title": title, "thumb": thumb, "original": "https://o/x", "page": "https://commons.wikimedia.org/wiki/" + title, "width": width,
            "height": 1500, "mime": mime, "license_raw": lic, "license_url": "https://license", "author": author, "desc": desc, "cats": cats, "name": ""}


def test_candidate_filters():
    assert ms.candidate_ok(cand(), "Foo bar", False)[0]
    assert ms.candidate_ok(cand(lic="CC BY-NC 4.0"), "Foo bar", False) == (False, "license")
    assert ms.candidate_ok(cand(mime="image/svg+xml"), "Foo bar", False) == (False, "format")
    assert ms.candidate_ok(cand(mime="image/tiff"), "Foo bar", False) == (False, "format")
    assert ms.candidate_ok(cand(width=300), "Foo bar", False) == (False, "format")
    assert ms.candidate_ok(cand(author=""), "Foo bar", False) == (False, "author")


def test_search_results_must_mention_the_species():
    assert ms.candidate_ok(cand(title="File:Foo bar 1.jpg"), "Foo bar", True)[0]
    assert ms.candidate_ok(cand(title="File:Other thing.jpg"), "Foo bar", True) == (False, "not-this-species")
    # รูปที่มาจากหมวดหมู่ของชนิดนั้นเองไม่ต้องมีชื่อในชื่อไฟล์
    assert ms.candidate_ok(cand(title="File:IMG_0001.jpg"), "Foo bar", False)[0]


def test_microbes_prefer_micrographs_over_culture_plates():
    micro = cand(title="File:Foo bar SEM.jpg", desc="Scanning electron micrograph of cells", cats="Electron micrographs")
    plate = cand(title="File:Foo bar colonies on agar plate.jpg", desc="Petri dish with colonies on blood agar")
    assert ms.score_candidate(micro, True, "Foo bar") > ms.score_candidate(plate, True, "Foo bar")
    assert ms.pick_candidates([plate, micro], True, 1, "Foo bar")[0]["title"] == micro["title"]


def test_figures_diagrams_and_stereo_pairs_score_low():
    photo = cand(title="File:Foo bar.jpg")
    for bad in ("File:Foo bar life cycle.jpg", "File:Foo bar crossview 3D.jpg", "File:Foo bar diagram.png", "File:Foo-bar-g001.png",
                "File:Exosome secretion affects social motility in the species Foo bar in vitro today.png"):
        assert ms.score_candidate(cand(title=bad), False, "Foo bar") < ms.score_candidate(photo, False, "Foo bar"), bad


def test_featured_pictures_get_a_boost():
    plain = cand(title="File:Foo bar a.jpg")
    featured = cand(title="File:Foo bar b.jpg", cats="Featured pictures of animals")
    assert ms.score_candidate(featured, False, "Foo bar") > ms.score_candidate(plain, False, "Foo bar")


def test_pick_dedupes_and_limits():
    a, b = cand(title="File:A.jpg"), cand(title="File:B.jpg")
    assert len(ms.pick_candidates([a, a, b], False, 5)) == 2
    assert len(ms.pick_candidates([a, b], False, 1)) == 1


def test_is_microbe():
    assert ms.is_microbe({"id": "x", "group": "bacteria"}) and ms.is_microbe({"id": "x", "group": "archaea"})
    assert ms.is_microbe({"id": "x", "group": "fungi", "traits": {"form": "yeast"}})
    assert not ms.is_microbe({"id": "x", "group": "fungi", "traits": {"form": "mushroom"}})
    assert ms.is_microbe({"id": "euglena-gracilis", "group": "protists"})
    assert not ms.is_microbe({"id": "pyropia-yezoensis", "group": "protists"})
    assert not ms.is_microbe({"id": "x", "group": "plants"}) and not ms.is_microbe({"id": "x", "group": "animals"})


# ---------------------------------------------------------------- Commons จำลอง

def page(c):
    return {"title": c["title"], "imageinfo": [{
        "thumburl": c["thumb"], "url": c["original"], "descriptionurl": c["page"], "width": c["width"], "height": c["height"], "mime": c["mime"],
        "extmetadata": {"LicenseShortName": {"value": c["license_raw"]}, "LicenseUrl": {"value": c["license_url"]}, "Artist": {"value": c["author"]},
                        "ImageDescription": {"value": c["desc"]}, "Categories": {"value": c["cats"]}, "ObjectName": {"value": ""}}}]}


class FakeCommons:
    def __init__(self):
        self.calls = []
        self.category = {}   # ชื่อวิทยาศาสตร์ -> [cand]
        self.search = {}
        self.bytes_calls = []

    def __call__(self, url):
        self.calls.append(url)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if q.get("generator") == ["categorymembers"]:
            name = q["gcmtitle"][0].split(":", 1)[1]
            pages = [page(c) for c in self.category.get(name, [])]
        else:
            name = q["gsrsearch"][0].strip('"')
            pages = [page(c) for c in self.search.get(name, [])]
        return json.dumps({"query": {"pages": pages}})

    def get_bytes(self, url):
        self.bytes_calls.append(url)
        from PIL import Image
        buf = io.BytesIO()
        Image.effect_noise((1800, 1200), 60).convert("RGB").save(buf, "JPEG", quality=95)
        return buf.getvalue()


@pytest.fixture
def world(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    ds.write()
    api = FakeCommons()
    fx = ms.Fetcher(str(tmp_path / "cache"), getter=api, bytes_getter=api.get_bytes, intervals={})
    return ds, api, fx, tmp_path


def run_images(ds, fx, tmp_path, *extra):
    args = ms.build_parser().parse_args(["images", "--data", ds.root, "--cache", str(tmp_path / "cache"), "--images-dir", str(tmp_path / "site" / "images"),
                                         "--missing-report", str(tmp_path / "reports" / "images-missing.md"), *extra])
    return ms.cmd_images(args, fetcher=fx), args


def orgs(ds):
    return {o["id"]: o for o in ms.load_organisms(ds.root)}


def test_find_candidates_merges_category_and_search_and_counts_rejections(world):
    ds, api, fx, tmp = world
    api.category["Escherichia coli"] = [cand(title="File:A.jpg"), cand(title="File:B.jpg", lic="CC BY-NC 4.0")]
    api.search["Escherichia coli"] = [cand(title="File:A.jpg"), cand(title="File:Escherichia coli C.jpg"), cand(title="File:Unrelated.jpg")]
    good, rejected, seen = ms.find_candidates(fx, "Escherichia coli")
    assert sorted(c["title"] for c in good) == ["File:A.jpg", "File:Escherichia coli C.jpg"]
    assert rejected == {"license": 1, "not-this-species": 1} and seen == 4


def test_images_command_saves_webp_with_credit_and_updates_data(world):
    pytest.importorskip("PIL")
    ds, api, fx, tmp = world
    api.category["Escherichia coli"] = [cand(title="File:Escherichia coli SEM.jpg", desc="scanning electron micrograph", author="Jane Doe", lic="CC BY-SA 4.0")]
    rc, args = run_images(ds, fx, tmp, "--only", "escherichia-coli")
    assert rc == 0
    img = orgs(ds)["escherichia-coli"]["images"][0]
    assert img["url"] == "images/escherichia-coli/1.webp" and img["author"] == "Jane Doe" and img["license"] == "CC BY-SA 4.0"
    assert img["source_url"] == "https://commons.wikimedia.org/wiki/File:Escherichia coli SEM.jpg" and img["kind"] == "micrograph"
    path = tmp / "site" / "images" / "escherichia-coli" / "1.webp"
    raw = path.read_bytes()
    assert raw[:4] == b"RIFF" and raw[8:12] == b"WEBP" and len(raw) <= ms.MAX_IMAGE_BYTES
    from PIL import Image
    assert Image.open(path).width <= ms.MAX_IMAGE_WIDTH
    # รูปที่ไม่ได้ขอ (--only) ไม่ถูกแตะ
    assert orgs(ds)["plasmodium-falciparum"]["images"] == []
    assert ms.validate_data(ds.root).errors == []


def test_second_run_uses_cache_and_skips_species_with_images(world):
    pytest.importorskip("PIL")
    ds, api, fx, tmp = world
    api.category["Escherichia coli"] = [cand(title="File:Escherichia coli.jpg")]
    run_images(ds, fx, tmp)
    first_calls = len(api.calls) + len(api.bytes_calls)
    fx2 = ms.Fetcher(str(tmp / "cache"), getter=api, bytes_getter=api.get_bytes, intervals={})
    run_images(ds, fx2, tmp)
    assert len(api.calls) + len(api.bytes_calls) == first_calls  # ไม่ยิงเพิ่ม
    # --redo เลือกใหม่ แต่ยังใช้ cache (ไม่ยิง API ซ้ำ)
    fx3 = ms.Fetcher(str(tmp / "cache"), getter=api, bytes_getter=api.get_bytes, intervals={})
    run_images(ds, fx3, tmp, "--redo")
    assert len(api.calls) + len(api.bytes_calls) == first_calls and fx3.stats["api"] == 0


def test_species_without_acceptable_image_is_listed_with_reason(world):
    pytest.importorskip("PIL")
    ds, api, fx, tmp = world
    api.category["Escherichia coli"] = [cand(title="File:NC.jpg", lic="CC BY-NC 4.0")]
    rc, args = run_images(ds, fx, tmp)
    assert rc == 0 and orgs(ds)["escherichia-coli"]["images"] == []
    report = open(args.missing_report, encoding="utf-8").read()
    assert "`escherichia-coli`" in report and "`plasmodium-falciparum`" in report
    assert "license 1" in report and "ไม่พบรูปในหมวดหมู่" in report
    assert "ไม่มีรูป 2 ชนิด" in report


def test_download_failure_tries_the_next_candidate(world):
    pytest.importorskip("PIL")
    ds, api, fx, tmp = world
    api.category["Escherichia coli"] = [cand(title="File:Escherichia coli good.jpg", thumb="https://t/bad"), cand(title="File:Escherichia coli ok.jpg", thumb="https://t/ok")]
    real = api.get_bytes

    def flaky(url):
        if url.endswith("/bad"):
            raise OSError("boom")
        return real(url)
    fx.bytes_getter = flaky
    fx.retries = 1
    run_images(ds, fx, tmp, "--only", "escherichia-coli")
    assert orgs(ds)["escherichia-coli"]["images"][0]["title"] == "File:Escherichia coli ok.jpg"


def test_big_images_are_shrunk_under_the_limit(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    buf = io.BytesIO()
    Image.effect_noise((3000, 2000), 90).convert("RGB").save(buf, "JPEG", quality=98)  # ภาพสัญญาณรบกวนบีบอัดยาก
    w, h, size = ms.to_webp(buf.getvalue(), str(tmp_path / "x" / "1.webp"))
    assert size <= ms.MAX_IMAGE_BYTES and w <= ms.MAX_IMAGE_WIDTH
    assert os.path.getsize(tmp_path / "x" / "1.webp") == size


# ---------------------------------------------------------------- images --check

def good_image(oid="escherichia-coli"):
    return {"url": "images/%s/1.webp" % oid, "author": "Jane Doe", "license": "CC BY 4.0", "license_url": "https://l", "source_url": "https://commons.wikimedia.org/wiki/File:X.jpg"}


def webp_bytes(n=2000):
    return b"RIFF" + (n - 8).to_bytes(4, "little") + b"WEBP" + b"\0" * (n - 12)


@pytest.fixture
def checked(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    (tmp_path / "site" / "images" / "escherichia-coli").mkdir(parents=True)
    (tmp_path / "site" / "images" / "escherichia-coli" / "1.webp").write_bytes(webp_bytes())
    ds.files["bacteria"][0]["images"] = [good_image()]
    ds.write()
    report = tmp_path / "reports" / "images-missing.md"
    report.parent.mkdir()
    report.write_text("| *Plasmodium falciparum* (`plasmodium-falciparum`) | protists | x |", encoding="utf-8")
    return ds, tmp_path


def run_check(ds, tmp, capsys):
    args = ms.build_parser().parse_args(["images", "--check", "--data", ds.root, "--images-dir", str(tmp / "site" / "images"),
                                         "--missing-report", str(tmp / "reports" / "images-missing.md")])
    rc = ms.cmd_images_check(args)
    return rc, capsys.readouterr().out


def test_check_passes_for_a_good_dataset(checked, capsys):
    ds, tmp = checked
    rc, out = run_check(ds, tmp, capsys)
    assert rc == 0 and "ผ่าน" in out and "ปัญหา 0" in out


@pytest.mark.parametrize("field", ["url", "author", "license", "source_url"])
def test_check_requires_every_credit_field(checked, capsys, field):
    ds, tmp = checked
    ds.files["bacteria"][0]["images"][0][field] = ""
    ds.write()
    rc, out = run_check(ds, tmp, capsys)
    assert rc == 1 and field in out


def test_check_rejects_a_non_open_license(checked, capsys):
    ds, tmp = checked
    ds.files["bacteria"][0]["images"][0]["license"] = "CC BY-NC 4.0"
    ds.write()
    rc, out = run_check(ds, tmp, capsys)
    assert rc == 1 and "ไม่อยู่ในที่อนุญาต" in out
    assert "IMAGE_LICENSE" in ms.validate_data(ds.root).codes()  # validate ก็จับได้เหมือนกัน


def test_check_rejects_missing_oversized_and_non_webp_files(checked, capsys):
    ds, tmp = checked
    path = tmp / "site" / "images" / "escherichia-coli" / "1.webp"
    path.write_bytes(webp_bytes(ms.MAX_IMAGE_BYTES + 5000))
    rc, out = run_check(ds, tmp, capsys)
    assert rc == 1 and "เกิน 500 KB" in out
    path.write_bytes(b"\xff\xd8\xff jpeg bytes")
    rc, out = run_check(ds, tmp, capsys)
    assert rc == 1 and "ไม่ใช่ WebP" in out
    path.unlink()
    rc, out = run_check(ds, tmp, capsys)
    assert rc == 1 and "ไม่พบไฟล์" in out


def test_check_rejects_wrong_extension_and_foreign_source(checked, capsys):
    ds, tmp = checked
    ds.files["bacteria"][0]["images"][0]["url"] = "images/escherichia-coli/1.jpg"
    ds.files["bacteria"][0]["images"][0]["source_url"] = "https://example.com/pic"
    ds.write()
    rc, out = run_check(ds, tmp, capsys)
    assert rc == 1 and ".webp" in out and "Commons" in out


def test_check_flags_orphan_files(checked, capsys):
    ds, tmp = checked
    (tmp / "site" / "images" / "escherichia-coli" / "2.webp").write_bytes(webp_bytes())
    rc, out = run_check(ds, tmp, capsys)
    assert rc == 1 and "ไฟล์เกิน" in out and "2.webp" in out


def test_check_requires_species_without_images_to_be_in_the_report(checked, capsys):
    ds, tmp = checked
    (tmp / "reports" / "images-missing.md").write_text("(empty)", encoding="utf-8")
    rc, out = run_check(ds, tmp, capsys)
    assert rc == 1 and "plasmodium-falciparum" in out and "ไม่อยู่ใน" in out
