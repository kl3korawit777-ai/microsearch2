"""ทดสอบ fetch-traits (BacDive v2, IUCN v4) และ traits-diff ด้วย API จำลอง ไม่ยิงเน็ตจริง ไม่ใช้ token จริง"""

import json
import os
import sys
import urllib.error

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
sys.path.insert(0, HERE)
import microsearch as ms  # noqa: E402
from test_validate import Dataset  # noqa: E402

TOKEN = "rlts_TESTSECRET0123456789"


def bd_record(bid, species="Escherichia coli", type_strain="yes", **extra):
    rec = {"General": {"BacDive-ID": bid}, "Name and taxonomic classification": {"species": species, "type strain": type_strain},
           "Morphology": {"cell morphology": [{"@ref": 1, "gram stain": "negative", "cell shape": "rod-shaped", "motility": "yes", "flagellum arrangement": "peritrichous"}]},
           "Physiology and metabolism": {"oxygen tolerance": [{"@ref": 1, "oxygen tolerance": "facultative anaerobe"}],
                                         "spore formation": {"@ref": 1, "spore formation": "no"},
                                         "halophily": [{"@ref": 2, "salt": "NaCl", "growth": "positive", "tested relation": "growth", "concentration": "0-5 %"},
                                                       {"@ref": 2, "salt": "NaCl", "growth": "positive", "tested relation": "optimum", "concentration": "2 %"},
                                                       {"@ref": 2, "salt": "KCl", "growth": "positive", "concentration": "9 %"}]},
           "Culture and growth conditions": {"culture temp": [{"growth": "positive", "type": "growth", "temperature": "15-45"},
                                                              {"growth": "positive", "type": "optimum", "temperature": "37"}],
                                             "culture pH": [{"ability": "positive", "type": "growth", "pH": "6-8"}, {"ability": "no", "type": "growth", "pH": "3"}]}}
    rec.update(extra)
    return rec


class FakeApi:
    """คำตอบจำลองของ BacDive และ IUCN: เก็บจำนวนคำขอและหัวข้อ Authorization ที่ได้รับ"""

    def __init__(self):
        self.taxa, self.strains, self.iucn, self.calls, self.auth = {}, {}, {}, [], []

    def bacdive(self, url):
        self.calls.append(url)
        rest = url.split("/v2/", 1)[1]
        if rest.startswith("taxon/"):
            path, _, q = rest.partition("?")
            _, genus, species = path.split("/")
            ids = self.taxa.get((genus, species))
            if ids is None:
                raise urllib.error.HTTPError(url, 404, "nf", {}, None)
            page = int(q.split("=")[1]) if q else 0
            chunk = ids[page * 3:(page + 1) * 3]
            nxt = "%s/taxon/%s/%s?page=%d" % (ms.BACDIVE_API, genus, species, page + 1) if (page + 1) * 3 < len(ids) else None
            return json.dumps({"count": len(ids), "next": nxt, "previous": None, "results": chunk})
        ids = [int(x) for x in rest.split("/", 1)[1].split(";")]
        return json.dumps({"count": len(ids), "next": None, "previous": None, "results": {str(i): self.strains[i] for i in ids}})

    def iucn_get(self, url, token=TOKEN):
        self.calls.append(url)
        self.auth.append(token)
        if token != TOKEN:
            raise urllib.error.HTTPError(url, 401, "unauthorized", {}, None)
        q = dict(p.split("=") for p in url.split("?", 1)[1].split("&"))
        got = self.iucn.get((q["genus_name"], q["species_name"]))
        if got is None:
            raise urllib.error.HTTPError(url, 404, "nf", {}, None)
        return json.dumps(got)


def bd_fetcher(tmp, api):
    return ms.Fetcher(str(tmp / "cache"), getter=api.bacdive, intervals={})


# ---------------------------------------------------------------- ฟังก์ชันย่อย

def test_parse_numbers_and_salt_percent():
    assert ms.parse_numbers("25-45") == (25.0, 45.0) and ms.parse_numbers("37") == (37.0, 37.0) and ms.parse_numbers("ไม่มี") is None
    assert ms.salt_percent("2.5 %") == (2.5, 2.5)
    assert ms.salt_percent("100 g/L") == (10.0, 10.0)
    assert ms.salt_percent("1 M")[0] == pytest.approx(5.844)
    assert ms.salt_percent("10") is None and ms.salt_percent("x") is None


@pytest.mark.parametrize("t,want", [(4, "psychro"), (19.9, "psychro"), (20, "meso"), (37, "meso"), (45, "meso"), (46, "thermo"), (80, "thermo"), (95, "hyper")])
def test_temp_category(t, want):
    assert ms.temp_category(t) == want


@pytest.mark.parametrize("rec,name,want", [
    ("Escherichia coli", "Escherichia coli", True), ("escherichia COLI", "Escherichia coli", True),
    ("Salmonella enterica subsp. enterica", "Salmonella enterica", True), ("Salmonella enterica subsp. indica", "Salmonella enterica", False),
    ("Escherichia fergusonii", "Escherichia coli", False), (None, "Escherichia coli", False),
])
def test_bacdive_same_species(rec, name, want):
    assert ms.bacdive_same_species(rec, name) is want


def test_normalize_bacdive_maps_values_and_keeps_raw():
    t = ms.normalize_bacdive(bd_record(1))
    assert t["shape"] == {"value": "rod", "raw": "rod-shaped"} and t["gram"]["value"] == "neg" and t["oxy"]["value"] == "fac"
    assert t["motility"]["value"] == "flagella" and t["endospore"]["value"] == "no"
    assert t["temp"]["value"] == {"min": 15.0, "max": 45.0, "unit": "°C"} and t["temp_opt"]["value"] == "meso"
    assert t["ph"]["value"] == {"min": 6.0, "max": 8.0, "unit": "pH"}               # ค่า pH ที่ ability=no ไม่นับ
    assert t["salinity"]["value"] == {"min": 0.0, "max": 5.0, "unit": "% NaCl"}      # เฉพาะ NaCl (KCl ไม่นับ)


def test_normalize_bacdive_unmapped_values_have_no_value_but_keep_raw():
    rec = bd_record(1)
    rec["Morphology"]["cell morphology"] = {"cell shape": "ovoid-shaped", "gram stain": "variable", "motility": "yes"}
    rec["Physiology and metabolism"]["spore formation"] = {"spore formation": "yes", "type of spore": "conidium"}
    t = ms.normalize_bacdive(rec)
    assert t["shape"] == {"value": None, "raw": "ovoid-shaped"} and t["gram"]["value"] is None
    assert t["motility"]["value"] is None and t["endospore"]["value"] is None and "conidium" in t["endospore"]["raw"]


def test_normalize_bacdive_missing_sections_give_empty():
    assert ms.normalize_bacdive({"General": {}}) == {}


def test_load_env_reads_file_and_environment_wins(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("# comment\nIUCN_TOKEN=\"abc\"\nOTHER = x\n", encoding="utf-8")
    monkeypatch.delenv("IUCN_TOKEN", raising=False)
    assert ms.load_env(str(f))["IUCN_TOKEN"] == "abc"
    monkeypatch.setenv("IUCN_TOKEN", "fromenv")
    assert ms.load_env(str(f))["IUCN_TOKEN"] == "fromenv"
    assert ms.load_env(str(tmp_path / "none")) == {"IUCN_TOKEN": "fromenv"}


# ---------------------------------------------------------------- BacDive

def test_fetch_bacdive_pages_ids_and_finds_type_strain_in_a_later_chunk(tmp_path, monkeypatch):
    monkeypatch.setattr(ms, "BACDIVE_CHUNK", 2)
    api = FakeApi()
    api.taxa[("Escherichia", "coli")] = [10, 11, 12, 13, 14, 15, 16]          # 3 หน้า (หน้าละ 3 ใน FakeApi)
    api.strains = {i: bd_record(i, type_strain="no") for i in api.taxa[("Escherichia", "coli")]}
    api.strains[15] = bd_record(15)
    e = ms.fetch_bacdive(bd_fetcher(tmp_path, api), "Escherichia coli")
    assert e["type_strain_id"] == 15 and e["n_strains"] == 7 and e["url"] == "https://bacdive.dsmz.de/strain/15" and e["traits"]["gram"]["value"] == "neg"
    fetches = [c for c in api.calls if "/fetch/" in c]
    assert len(fetches) == 3 and not any("16" in c.split("/fetch/")[1].split(";") for c in fetches[:2])   # หยุดทันทีที่เจอ ไม่ดึงที่เหลือ


def test_fetch_bacdive_second_run_uses_cache_only(tmp_path):
    api = FakeApi()
    api.taxa[("Escherichia", "coli")] = [1]
    api.strains = {1: bd_record(1)}
    fx = bd_fetcher(tmp_path, api)
    ms.fetch_bacdive(fx, "Escherichia coli")
    n = len(api.calls)
    fx2 = bd_fetcher(tmp_path, api)
    e = ms.fetch_bacdive(fx2, "Escherichia coli")
    assert len(api.calls) == n and fx2.stats["api"] == 0 and fx2.stats["cache"] >= 2 and e["type_strain_id"] == 1


def test_fetch_bacdive_refresh_calls_the_api_again(tmp_path):
    api = FakeApi()
    api.taxa[("Escherichia", "coli")] = [1]
    api.strains = {1: bd_record(1)}
    ms.fetch_bacdive(bd_fetcher(tmp_path, api), "Escherichia coli")
    n = len(api.calls)
    ms.fetch_bacdive(ms.Fetcher(str(tmp_path / "cache"), refresh=True, getter=api.bacdive, intervals={}), "Escherichia coli")
    assert len(api.calls) == 2 * n


def test_fetch_bacdive_unknown_name_and_no_type_strain_are_notes_not_guesses(tmp_path):
    api = FakeApi()
    api.taxa[("Foo", "bar")] = [1, 2]
    api.strains = {1: bd_record(1, "Foo bar", "no"), 2: bd_record(2, "Foo baz", "yes")}
    e = ms.fetch_bacdive(bd_fetcher(tmp_path, api), "Foo bar")
    assert e["type_strain_id"] is None and e["traits"] == {} and "ไม่มี type strain" in e["note"] and "Foo baz" in e["note"]
    e = ms.fetch_bacdive(bd_fetcher(tmp_path, api), "No such")
    assert e["type_strain_id"] is None and "ไม่พบชื่อนี้" in e["note"] and e["n_strains"] == 0


# ---------------------------------------------------------------- IUCN

def iucn_doc(*assessments):
    return {"taxon": {"sis_id": 1}, "assessments": list(assessments)}


def assess(year, code, latest=True, scope="Global", url=None):
    return {"year_published": str(year), "latest": latest, "red_list_category_code": code, "assessment_id": year,
            "url": url or "https://www.iucnredlist.org/species/1/%d" % year, "scopes": [{"description": {"en": scope}}]}


def iucn_fx(tmp, api, token=TOKEN):
    return ms.Fetcher(str(tmp / "cache"), getter=lambda u: api.iucn_get(u, token), intervals={})


def test_fetch_iucn_takes_the_latest_global_assessment(tmp_path):
    api = FakeApi()
    api.iucn[("Aedes", "aegypti")] = iucn_doc(assess(2008, "LC", latest=False), assess(2019, "VU", scope="Europe"), assess(2021, "NT"))
    e = ms.fetch_iucn(iucn_fx(tmp_path, api), "Aedes aegypti")
    assert (e["category"], e["assessed"], e["url"]) == ("NT", "2021", "https://www.iucnredlist.org/species/1/2021")
    assert api.calls[0].startswith(ms.IUCN_API + "/taxa/scientific_name?") and "genus_name=Aedes" in api.calls[0] and "species_name=aegypti" in api.calls[0]


def test_fetch_iucn_missing_and_odd_cases(tmp_path):
    api = FakeApi()
    api.iucn[("A", "empty")] = iucn_doc()
    api.iucn[("A", "odd")] = iucn_doc(assess(2020, "ZZ"))
    api.iucn[("A", "http")] = iucn_doc(assess(2020, "EN", url="http://www.iucnredlist.org/species/9/9"))
    fx = iucn_fx(tmp_path, api)
    assert ms.fetch_iucn(fx, "A none")["note"] == "ไม่พบชื่อนี้ใน IUCN"
    assert "ยังไม่มีการประเมิน" in ms.fetch_iucn(fx, "A empty")["note"]
    odd = ms.fetch_iucn(fx, "A odd")
    assert odd["category"] is None and "ไม่รู้จัก" in odd["note"]
    assert ms.fetch_iucn(fx, "A http")["url"] == "https://www.iucnredlist.org/species/9/9"     # บังคับ https


def test_fetch_iucn_rejected_token_raises_auth_error(tmp_path):
    api = FakeApi()
    with pytest.raises(ms.IucnAuthError):
        ms.fetch_iucn(iucn_fx(tmp_path, api, token="wrong"), "Aedes aegypti")


# ---------------------------------------------------------------- คำสั่ง

def run_fetch(ds, tmp, api, *extra, iucn_token=TOKEN, env=None):
    args = ms.build_parser().parse_args(["fetch-traits", "--data", ds.root, "--cache", str(tmp / "cache"), *extra])
    return ms.cmd_fetch_traits(args, fetcher=bd_fetcher(tmp, api), iucn_fetcher=iucn_fx(tmp, api, iucn_token), env=env if env is not None else {"IUCN_TOKEN": TOKEN})


def organisms_bytes(ds):
    root = os.path.join(ds.root, "organisms")
    return {n: open(os.path.join(root, n), "rb").read() for n in sorted(os.listdir(root))}


def world(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    ds.groups["groups"].append({"id": "animals", "th": "สัตว์", "en": "Animals", "ranks": [{"th": "โดเมน", "en": "Domain"}, {"th": "สกุล", "en": "Genus"}], "traits": []})
    ds.write()
    api = FakeApi()
    api.taxa[("Escherichia", "coli")] = [1]
    api.strains = {1: bd_record(1)}
    return ds, api


def test_fetch_traits_writes_generated_file_and_never_touches_organisms(tmp_path):
    ds, api = world(tmp_path)
    before = organisms_bytes(ds)
    assert run_fetch(ds, tmp_path, api, "--source", "bacdive") == 0
    assert organisms_bytes(ds) == before
    got = json.load(open(ms.traits_fetched_path(ds.root), encoding="utf-8"))
    e = got["organisms"]["escherichia-coli"]["bacdive"]
    assert e["type_strain_id"] == 1 and e["traits"]["gram"] == {"value": "neg", "raw": "negative"} and got["sources"]["bacdive"] == ms.BACDIVE_API
    assert "plasmodium-falciparum" not in got["organisms"] or "bacdive" not in got["organisms"]["plasmodium-falciparum"]   # ไม่ใช่กลุ่มของ BacDive


def test_fetch_traits_second_run_makes_no_api_calls(tmp_path, capsys):
    ds, api = world(tmp_path)
    run_fetch(ds, tmp_path, api, "--source", "bacdive")
    n = len(api.calls)
    run_fetch(ds, tmp_path, api, "--source", "bacdive")
    assert len(api.calls) == n
    assert "เรียก API 0 ครั้ง" in capsys.readouterr().out


def test_fetch_traits_uses_accepted_name_when_textbook_name_is_missing(tmp_path):
    ds, api = world(tmp_path)
    ds.files["bacteria"][0]["accepted_name"] = "Escherichia vulgaris"
    ds.write()
    api.taxa = {("Escherichia", "vulgaris"): [1]}
    run_fetch(ds, tmp_path, api, "--source", "bacdive")
    e = json.load(open(ms.traits_fetched_path(ds.root), encoding="utf-8"))["organisms"]["escherichia-coli"]["bacdive"]
    assert e["query"] == "Escherichia vulgaris"
    api.strains[1]["Name and taxonomic classification"]["species"] = "Escherichia vulgaris"


def test_fetch_traits_stops_iucn_after_the_first_rejection(tmp_path, capsys):
    ds, api = world(tmp_path)
    ds.files["protists"][0]["group"] = "animals"        # ใช้ชนิดนี้เป็นสัตว์สองตัว
    second = dict(ds.files["protists"][0], id="plasmodium-vivax", scientific_name="Plasmodium vivax")
    ds.files["animals"] = [ds.files["protists"].pop(0), second]
    ds.write()
    rc = run_fetch(ds, tmp_path, api, "--source", "iucn", iucn_token="wrong")
    assert rc == 2
    assert len([c for c in api.calls if "iucnredlist" in c or "genus_name" in c]) == 1       # ไม่ยิงซ้ำรายการที่เหลือ
    out = capsys.readouterr().out
    assert "ปฏิเสธ token" in out and "wrong" not in out
    assert "iucn_error" in json.load(open(ms.traits_fetched_path(ds.root), encoding="utf-8"))


def test_fetch_traits_without_token_skips_iucn_but_runs_bacdive(tmp_path, capsys):
    ds, api = world(tmp_path)
    args = ms.build_parser().parse_args(["fetch-traits", "--data", ds.root, "--cache", str(tmp_path / "cache")])
    assert ms.cmd_fetch_traits(args, fetcher=bd_fetcher(tmp_path, api), env={}) == 0
    out = capsys.readouterr().out
    assert "ไม่มี IUCN_TOKEN" in out and "[bacdive] escherichia-coli" in out


def test_token_never_reaches_cache_output_or_logs(tmp_path, capsys):
    ds, api = world(tmp_path)
    ds.files["animals"] = [dict(ds.files["protists"].pop(0), group="animals", id="aedes-aegypti", scientific_name="Aedes aegypti")]
    ds.write()
    api.iucn[("Aedes", "aegypti")] = iucn_doc(assess(2021, "LC"))
    assert run_fetch(ds, tmp_path, api) == 0
    seen = capsys.readouterr().out
    blobs = [seen, open(ms.traits_fetched_path(ds.root), encoding="utf-8").read()]
    for root, _, files in os.walk(str(tmp_path)):
        for f in files:
            blobs.append(open(os.path.join(root, f), encoding="utf-8", errors="ignore").read())
    assert not any(TOKEN in b for b in blobs)
    assert api.auth == [TOKEN]


def test_cache_key_does_not_depend_on_the_token(tmp_path):
    ds, api = world(tmp_path)
    fx = ms.Fetcher(str(tmp_path / "cache"), getter=lambda u: "{}", intervals={})
    url = ms.IUCN_API + "/taxa/scientific_name?genus_name=A&species_name=b"
    assert TOKEN not in fx.cache_path("iucn", "taxon-A b", url, "json")


# ---------------------------------------------------------------- traits-diff

def write_fetched(ds, organisms, **extra):
    os.makedirs(os.path.join(ds.root, "generated"), exist_ok=True)
    json.dump({"organisms": organisms, **extra}, open(ms.traits_fetched_path(ds.root), "w", encoding="utf-8"), ensure_ascii=False)


def test_traits_diff_categories(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    o = ds.files["bacteria"][0]
    o["traits"] = {"shape": "rod", "gram": "pos", "oxy": "aer", "endospore": "yes"}
    ds.write()
    t = ms.normalize_bacdive(bd_record(1))
    t.pop("endospore")                                               # API ไม่มี endospore แต่เรามี
    t["motility"] = {"value": None, "raw": "yes"}                    # เราว่าง API มีแต่แปลงไม่ได้
    t["temp_opt"] = {"value": "meso", "raw": "optimum 37 °C"}
    write_fetched(ds, {"escherichia-coli": {"bacdive": {"type_strain_id": 1, "url": "https://bacdive.dsmz.de/strain/1", "traits": t}}})
    d = ms.traits_diff_data(ds.root)
    by = {r["trait"]: r["cat"] for r in d["rows"] if r["id"] == "escherichia-coli"}
    assert by == {"shape": "same", "gram": "differ", "oxy": "differ", "endospore": "missing", "motility": "fill", "topt": "fill"}
    assert [r["api"] for r in d["rows"] if r["trait"] == "motility"][0].startswith("(ยังแปลงเป็นค่าของเราไม่ได้)")
    assert d["summary"] == {"same": 1, "differ": 2, "missing": 1, "fill": 2}


def test_traits_diff_range_traits_and_species_without_record(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    ds.groups["groups"][0]["id"] = "archaea"
    ds.files = {"archaea": [dict(ds.files["bacteria"][0], id="escherichia-coli", group="archaea", traits={"shape": "rod", "temp": {"min": 15.0, "max": 45.0, "unit": "°C"}})]}
    ds.write()
    t = ms.normalize_bacdive(bd_record(1))
    write_fetched(ds, {"escherichia-coli": {"bacdive": {"type_strain_id": 1, "url": "u", "traits": t}}})
    rows = {r["trait"]: r for r in ms.traits_diff_data(ds.root)["rows"]}
    assert rows["temp"]["cat"] == "same" and rows["ph"]["cat"] == "fill" and rows["salinity"]["cat"] == "fill"
    write_fetched(ds, {"escherichia-coli": {"bacdive": {"type_strain_id": None, "note": "ไม่พบชื่อนี้ใน BacDive", "traits": {}}}})
    d = ms.traits_diff_data(ds.root)
    assert {r["cat"] for r in d["rows"]} == {"missing"} and d["no_record"] == [("escherichia-coli", "bacdive", "ไม่พบชื่อนี้ใน BacDive")]


def test_traits_diff_iucn(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    ds.files = {"animals": [dict(ds.files["bacteria"][0], id="a-one", group="animals", scientific_name="A one"),
                            dict(ds.files["bacteria"][0], id="a-two", group="animals", scientific_name="A two", iucn={"category": "LC", "url": "https://x.org", "assessed": "2020"}),
                            dict(ds.files["bacteria"][0], id="a-three", group="animals", scientific_name="A three", iucn={"category": "LC", "url": "https://x.org", "assessed": "2020"}),
                            dict(ds.files["bacteria"][0], id="a-four", group="animals", scientific_name="A four")]}
    ds.write()
    ok = lambda c: {"iucn": {"category": c, "assessed": "2021", "url": "https://www.iucnredlist.org/species/1/2", "note": ""}}
    write_fetched(ds, {"a-one": ok("EN"), "a-two": ok("LC"), "a-three": ok("VU"), "a-four": {"iucn": {"category": None, "note": "ไม่พบชื่อนี้ใน IUCN"}}})
    d = ms.traits_diff_data(ds.root)
    assert {r["id"]: r["cat"] for r in d["rows"]} == {"a-one": "fill", "a-two": "same", "a-three": "differ"}
    assert d["no_record"] == [("a-four", "iucn", "ไม่พบชื่อนี้ใน IUCN")]


def test_traits_diff_reports_a_rejected_token_as_reason(tmp_path):
    ds = Dataset(str(tmp_path / "data"))
    ds.files = {"animals": [dict(ds.files["bacteria"][0], id="a-one", group="animals", scientific_name="A one")]}
    ds.write()
    write_fetched(ds, {}, iucn_error="IUCN ปฏิเสธ token (HTTP 401)")
    assert "ปฏิเสธ token" in ms.traits_diff_data(ds.root)["no_record"][0][2]


def test_traits_diff_command_writes_report_and_does_not_change_data(tmp_path, capsys):
    ds = Dataset(str(tmp_path / "data"))
    ds.write()
    t = ms.normalize_bacdive(bd_record(1))
    write_fetched(ds, {"escherichia-coli": {"bacdive": {"type_strain_id": 1, "url": "https://bacdive.dsmz.de/strain/1", "traits": t}}})
    before = organisms_bytes(ds)
    out = str(tmp_path / "reports" / "traits-diff.md")
    args = ms.build_parser().parse_args(["traits-diff", "--data", ds.root, "--out", out])
    assert ms.cmd_traits_diff(args) == 0
    text = open(out, encoding="utf-8").read()
    for label in ("ตรงกัน", "เราว่างแต่ API มี", "ต่างกัน", "API ไม่มี"):
        assert "## %s" % label in text
    assert "[rod-shaped](https://bacdive.dsmz.de/strain/1)" in text and organisms_bytes(ds) == before
    assert "ตรงกัน" in capsys.readouterr().out
