"""ทดสอบ fetch (cache, อัตราคำขอ, การไม่เดา id) และ taxonomy-diff ด้วย API จำลอง ไม่ยิงเน็ตจริง"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
sys.path.insert(0, HERE)
import microsearch as ms  # noqa: E402
from test_validate import Dataset  # noqa: E402


# ---------------------------------------------------------------- API จำลอง

def gbif_body(name, match="EXACT", rank="SPECIES", status="ACCEPTED", **over):
    d = {"usageKey": 111, "scientificName": name + " Auth", "canonicalName": name, "rank": rank, "status": status,
         "matchType": match, "kingdom": "Bacteria", "phylum": "Proteobacteria", "class": "Gammaproteobacteria",
         "order": "Enterobacterales", "family": "Enterobacteriaceae", "genus": name.split()[0]}
    d.update(over)
    return json.dumps(d)


def ncbi_xml(taxid, name, rank="species", lineage=(), synonyms=()):
    lin = "".join("<Taxon><TaxId>%d</TaxId><ScientificName>%s</ScientificName><Rank>%s</Rank></Taxon>" % (i + 10, n, r)
                  for i, (r, n) in enumerate(lineage))
    syn = "".join("<Synonym>%s</Synonym>" % s for s in synonyms)
    return ('<?xml version="1.0" ?><TaxaSet><Taxon><TaxId>%d</TaxId><ScientificName>%s</ScientificName>'
            "<OtherNames>%s<Name><ClassCDE>authority</ClassCDE><DispName>x</DispName></Name></OtherNames>"
            "<Rank>%s</Rank><LineageEx>%s</LineageEx></Taxon></TaxaSet>" % (taxid, name, syn, rank, lin))


class FakeApi:
    """เก็บบันทึกคำขอ และตอบตามตารางที่ test ตั้งไว้"""

    def __init__(self):
        self.calls = []
        self.gbif = {}    # ชื่อ -> body ของ species/match
        self.gbif_extra = {}  # path ย่อย -> body (species/<key>, species/<key>/synonyms)
        self.ncbi_ids = {}  # ชื่อ -> list ของ taxid
        self.ncbi_xml = {}  # taxid -> xml

    def __call__(self, url):
        self.calls.append(url)
        p = urllib.parse.urlparse(url)
        q = urllib.parse.parse_qs(p.query)
        if p.netloc == "api.gbif.org":
            if p.path.endswith("/species/match"):
                return self.gbif.get(q["name"][0], gbif_body(q["name"][0], match="NONE", rank="", status=""))
            return self.gbif_extra.get(p.path.split("/v1/")[1], '{"results": []}')
        if p.path.endswith("esearch.fcgi"):
            name = q["term"][0].split('"')[1]
            return json.dumps({"esearchresult": {"idlist": [str(i) for i in self.ncbi_ids.get(name, [])]}})
        return self.ncbi_xml[int(q["id"][0])]

    def reset(self):
        self.calls.clear()


@pytest.fixture
def api():
    return FakeApi()


def make_fetcher(tmp_path, api, **kw):
    return ms.Fetcher(str(tmp_path / "cache"), getter=api, intervals={}, **kw)


# ---------------------------------------------------------------- Fetcher / cache

def test_cache_avoids_second_request(tmp_path, api):
    fx = make_fetcher(tmp_path, api)
    url = "https://api.gbif.org/v1/species/match?name=A+b"
    api.gbif["A b"] = gbif_body("A b")
    first = fx.get("gbif", "match-A b", url)
    second = fx.get("gbif", "match-A b", url)
    assert first == second and len(api.calls) == 1
    assert fx.stats == {"api": 1, "cache": 1}


def test_refresh_ignores_cache(tmp_path, api):
    url = "https://api.gbif.org/v1/species/match?name=A+b"
    make_fetcher(tmp_path, api).get("gbif", "m", url)
    make_fetcher(tmp_path, api, refresh=True).get("gbif", "m", url)
    assert len(api.calls) == 2


def test_cache_stores_raw_response(tmp_path, api):
    fx = make_fetcher(tmp_path, api)
    url = "https://api.gbif.org/v1/species/match?name=A+b"
    api.gbif["A b"] = gbif_body("A b")
    fx.get("gbif", "m", url)
    path = fx.cache_path("gbif", "m", url, "json")
    with open(path, encoding="utf-8") as f:
        assert f.read() == api.gbif["A b"]


def test_errors_are_not_cached(tmp_path):
    calls = []

    def flaky(url):
        calls.append(url)
        raise urllib.error.HTTPError(url, 404, "nf", {}, None)

    fx = ms.Fetcher(str(tmp_path / "cache"), getter=flaky, intervals={})
    for _ in range(2):
        with pytest.raises(ms.FetchError):
            fx.get("gbif", "m", "https://x/y")
    assert len(calls) == 2  # 404 ไม่ retry และไม่ cache


def test_retries_transient_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    calls = []

    def flaky(url):
        calls.append(url)
        if len(calls) < 3:
            raise urllib.error.HTTPError(url, 503, "busy", {}, None)
        return "ok"

    fx = ms.Fetcher(str(tmp_path / "cache"), getter=flaky, intervals={})
    assert fx.get("ncbi", "m", "https://x/y") == "ok" and len(calls) == 3


def test_rate_limit_spacing(tmp_path, api):
    fx = ms.Fetcher(str(tmp_path / "cache"), getter=lambda u: "{}", intervals={"ncbi": 0.2})
    t0 = time.monotonic()
    for i in range(3):
        fx.get("ncbi", "q%d" % i, "https://eutils/x?i=%d" % i)
    assert time.monotonic() - t0 >= 0.39  # 3 คำขอ ห่างกันอย่างน้อย 0.2 วินาที 2 ช่วง


def test_real_ncbi_interval_is_at_most_three_per_second():
    assert ms.NCBI_MIN_INTERVAL >= 1 / 3


# ---------------------------------------------------------------- fetch_gbif

@pytest.mark.parametrize("match", ["FUZZY", "HIGHERRANK", "NONE"])
def test_gbif_inexact_match_gives_null_key(tmp_path, api, match):
    api.gbif["Foo bar"] = gbif_body("Foo bar", match=match)
    e = ms.fetch_gbif(make_fetcher(tmp_path, api), "Foo bar")
    assert e["key"] is None and e["lineage"] == {} and match in e["note"]


def test_gbif_non_species_rank_gives_null_key(tmp_path, api):
    api.gbif["Foo"] = gbif_body("Foo", rank="GENUS")
    assert ms.fetch_gbif(make_fetcher(tmp_path, api), "Foo")["key"] is None


def test_gbif_accepted_species(tmp_path, api):
    api.gbif["Foo bar"] = gbif_body("Foo bar", usageKey=5)
    api.gbif_extra["species/5/synonyms"] = json.dumps({"results": [{"canonicalName": "Old name"}, {"canonicalName": "Foo bar"}]})
    e = ms.fetch_gbif(make_fetcher(tmp_path, api), "Foo bar")
    assert (e["key"], e["accepted_key"], e["accepted_name"]) == (5, 5, "Foo bar")
    assert e["synonyms"] == ["Old name"] and e["lineage"]["family"] == "Enterobacteriaceae"


def test_gbif_synonym_resolves_accepted_name(tmp_path, api):
    api.gbif["Old name"] = gbif_body("Old name", usageKey=7, status="SYNONYM", acceptedUsageKey=9)
    api.gbif_extra["species/9"] = json.dumps({"canonicalName": "New name"})
    e = ms.fetch_gbif(make_fetcher(tmp_path, api), "Old name")
    assert (e["key"], e["accepted_key"], e["accepted_name"]) == (7, 9, "New name")


def test_gbif_doubtful_has_no_accepted_name(tmp_path, api):
    api.gbif["Foo bar"] = gbif_body("Foo bar", status="DOUBTFUL")
    e = ms.fetch_gbif(make_fetcher(tmp_path, api), "Foo bar")
    assert e["key"] == 111 and e["accepted_name"] is None and "DOUBTFUL" in e["note"]


# ---------------------------------------------------------------- fetch_ncbi

def test_ncbi_not_found(tmp_path, api):
    e = ms.fetch_ncbi(make_fetcher(tmp_path, api), "Foo bar")
    assert e["taxid"] is None and "ไม่พบ" in e["note"] and len(api.calls) == 1


def test_ncbi_ambiguous_gives_null(tmp_path, api):
    api.ncbi_ids["Foo bar"] = [1, 2]
    assert ms.fetch_ncbi(make_fetcher(tmp_path, api), "Foo bar")["taxid"] is None


def test_ncbi_non_species_rank_gives_null(tmp_path, api):
    api.ncbi_ids["Foo"] = [5]
    api.ncbi_xml[5] = ncbi_xml(5, "Foo", rank="genus")
    assert ms.fetch_ncbi(make_fetcher(tmp_path, api), "Foo")["taxid"] is None


def test_ncbi_parses_lineage_and_synonyms(tmp_path, api):
    api.ncbi_ids["Foo bar"] = [5]
    api.ncbi_xml[5] = ncbi_xml(5, "Foo bar", lineage=[("superkingdom", "Bacteria"), ("no rank", "Group"), ("genus", "Foo")],
                               synonyms=["Old name"])
    e = ms.fetch_ncbi(make_fetcher(tmp_path, api), "Foo bar")
    assert e["taxid"] == 5 and e["accepted_name"] == "Foo bar" and e["synonyms"] == ["Old name"]
    assert [x["rank"] for x in e["lineage"]] == ["domain", "no rank", "genus"]  # superkingdom -> domain


# ---------------------------------------------------------------- fetch (คำสั่ง) บนชุดข้อมูลจำลอง

ECOLI_LINEAGE = [("domain", "Bacteria"), ("phylum", "Pseudomonadota"), ("family", "Enterobacteriaceae"), ("genus", "Escherichia")]
PLASMO_LINEAGE = [("domain", "Eukaryota"), ("no rank", "Sar"), ("no rank", "Alveolata"), ("genus", "Plasmodium")]


def setup_world(tmp_path, api):
    ds = Dataset(str(tmp_path / "data"))
    ds.groups["groups"][0]["phyla"] = [{"name": "Proteobacteria", "new_name": "Pseudomonadota"}]
    ds.write()
    api.gbif["Escherichia coli"] = gbif_body("Escherichia coli", usageKey=1)
    api.ncbi_ids["Escherichia coli"] = [562]
    api.ncbi_xml[562] = ncbi_xml(562, "Escherichia coli", lineage=ECOLI_LINEAGE)
    api.gbif["Plasmodium falciparum"] = gbif_body("Plasmodium falciparum", match="FUZZY", usageKey=2)
    api.ncbi_ids["Plasmodium falciparum"] = [5833]
    api.ncbi_xml[5833] = ncbi_xml(5833, "Plasmodium falciparum", lineage=PLASMO_LINEAGE)
    return ds


def run_fetch(ds, tmp_path, api, *extra):
    args = ms.build_parser().parse_args(["fetch", "--data", ds.root, "--cache", str(tmp_path / "cache"), *extra])
    fx = ms.Fetcher(args.cache, args.refresh, getter=api, intervals={})
    return ms.cmd_fetch(args, fetcher=fx), fx


def read_fetched(ds):
    with open(ms.fetched_path(ds.root), encoding="utf-8") as f:
        return json.load(f)["organisms"]


def test_fetch_writes_ids_and_never_guesses(tmp_path, api):
    ds = setup_world(tmp_path, api)
    rc, _ = run_fetch(ds, tmp_path, api)
    assert rc == 0
    got = read_fetched(ds)
    assert got["escherichia-coli"]["gbif"]["key"] == 1 and got["escherichia-coli"]["ncbi"]["taxid"] == 562
    assert got["plasmodium-falciparum"]["gbif"]["key"] is None  # FUZZY -> null
    assert got["plasmodium-falciparum"]["ncbi"]["taxid"] == 5833


def test_fetch_second_run_uses_only_cache(tmp_path, api):
    ds = setup_world(tmp_path, api)
    run_fetch(ds, tmp_path, api)
    api.reset()
    rc, fx = run_fetch(ds, tmp_path, api)
    assert rc == 0 and api.calls == [] and fx.stats["api"] == 0 and fx.stats["cache"] > 0


def test_fetch_refresh_hits_api_again(tmp_path, api):
    ds = setup_world(tmp_path, api)
    run_fetch(ds, tmp_path, api)
    api.reset()
    run_fetch(ds, tmp_path, api, "--refresh")
    assert len(api.calls) > 0


def test_fetch_only_limits_and_merges(tmp_path, api):
    ds = setup_world(tmp_path, api)
    run_fetch(ds, tmp_path, api, "--only", "escherichia-coli")
    assert list(read_fetched(ds)) == ["escherichia-coli"]
    assert not any("Plasmodium" in u for u in api.calls)
    run_fetch(ds, tmp_path, api, "--only", "plasmodium-falciparum")
    assert list(read_fetched(ds)) == ["escherichia-coli", "plasmodium-falciparum"]


def test_fetch_unknown_only_id_fails(tmp_path, api):
    ds = setup_world(tmp_path, api)
    rc, _ = run_fetch(ds, tmp_path, api, "--only", "nope")
    assert rc == 1


def test_fetch_never_modifies_organisms_or_taxa(tmp_path, api):
    ds = setup_world(tmp_path, api)
    paths = [os.path.join(ds.root, p) for p in ("taxa.json", "groups.json", "organisms/bacteria.json", "organisms/protists.json")]
    before = [open(p, "rb").read() for p in paths]
    run_fetch(ds, tmp_path, api)
    assert before == [open(p, "rb").read() for p in paths]


def test_fetch_failure_is_reported_not_recorded_as_not_found(tmp_path, api, capsys):
    ds = setup_world(tmp_path, api)

    def broken(url):
        raise urllib.error.HTTPError(url, 404, "x", {}, None)

    args = ms.build_parser().parse_args(["fetch", "--data", ds.root, "--cache", str(tmp_path / "cache")])
    rc = ms.cmd_fetch(args, fetcher=ms.Fetcher(args.cache, getter=broken, intervals={}))
    assert rc == 1 and "ดึงไม่สำเร็จ" in capsys.readouterr().out
    assert read_fetched(ds)["escherichia-coli"]["gbif"] is None


# ---------------------------------------------------------------- taxonomy-diff

def diff(ds, tmp_path):
    out = str(tmp_path / "diff.md")
    args = ms.build_parser().parse_args(["taxonomy-diff", "--data", ds.root, "--out", out])
    assert ms.cmd_taxonomy_diff(args) == 0
    with open(out, encoding="utf-8") as f:
        return f.read()


def test_diff_report_lists_every_species_and_categories(tmp_path, api):
    ds = setup_world(tmp_path, api)
    run_fetch(ds, tmp_path, api)
    text = diff(ds, tmp_path)
    assert "Escherichia coli" in text and "Plasmodium falciparum" in text
    for title in ("ต่างกันจริง", "ชื่อใหม่ของชื่อเดียวกัน", "หาไม่เจอ", "ตรงกันหมด"):
        assert "## " + title in text


def test_diff_textbook_phylum_is_renamed_not_differ(tmp_path, api):
    ds = setup_world(tmp_path, api)
    run_fetch(ds, tmp_path, api)
    text = diff(ds, tmp_path)
    renamed = text.split("## ชื่อใหม่ของชื่อเดียวกัน")[1].split("## หาไม่เจอ")[0]
    assert "Proteobacteria" in renamed and "Pseudomonadota" in renamed and "คงชื่อตำรา" in renamed
    assert "Proteobacteria" not in text.split("## ต่างกันจริง")[1].split("## ชื่อใหม่")[0]


def test_diff_protist_uses_informal_clades_and_skips_supergroup(tmp_path, api):
    ds = setup_world(tmp_path, api)
    run_fetch(ds, tmp_path, api)
    text = diff(ds, tmp_path)
    # Eukarya=Eukaryota, SAR ไม่มีใน API (ข้าม), Alveolata พบเป็น no rank, Plasmodium ตรง => ตรงกันหมด
    match = text.split("## ตรงกันหมด")[1]
    assert "Plasmodium falciparum" in match
    assert "supergroup" not in text.split("## สรุป")[1].split("วิธีเทียบ")[0]


def test_diff_not_found_when_both_sources_null(tmp_path, api):
    ds = setup_world(tmp_path, api)
    api.ncbi_ids["Plasmodium falciparum"] = []
    run_fetch(ds, tmp_path, api)
    text = diff(ds, tmp_path)
    assert "Plasmodium falciparum" in text.split("## หาไม่เจอ")[1].split("## ตรงกันหมด")[0]


def test_diff_real_difference_with_both_sources_agreeing(tmp_path, api):
    ds = setup_world(tmp_path, api)
    api.gbif["Escherichia coli"] = gbif_body("Escherichia coli", usageKey=1, family="Morganellaceae")
    api.ncbi_xml[562] = ncbi_xml(562, "Escherichia coli",
                                 lineage=[("domain", "Bacteria"), ("phylum", "Pseudomonadota"), ("family", "Morganellaceae"),
                                          ("genus", "Escherichia")])
    run_fetch(ds, tmp_path, api)
    differ = diff(ds, tmp_path).split("## ต่างกันจริง")[1].split("## ชื่อใหม่")[0]
    assert "Enterobacteriaceae" in differ and "เสนอเปลี่ยนเป็น Morganellaceae" in differ


def test_diff_synonym_species_and_genus_move_is_renamed(tmp_path, api):
    ds = setup_world(tmp_path, api)
    api.gbif["Escherichia coli"] = gbif_body("Escherichia coli", usageKey=1, status="SYNONYM", acceptedUsageKey=3,
                                             genus="Newgenus")
    api.gbif_extra["species/3"] = json.dumps({"canonicalName": "Newgenus coli"})
    run_fetch(ds, tmp_path, api)
    text = diff(ds, tmp_path)
    renamed = text.split("## ชื่อใหม่ของชื่อเดียวกัน")[1].split("## หาไม่เจอ")[0]
    assert "Newgenus coli" in renamed
    assert "genus | Escherichia | Newgenus" in renamed  # สกุลที่ย้ายตามชื่อชนิดใหม่ ไม่ใช่ความต่างจริง


def test_diff_unknown_family_marker_is_flagged_with_proposal(tmp_path, api):
    ds = setup_world(tmp_path, api)
    ds.files["bacteria"][0]["lineage"][2]["name"] = "?"
    ds.write()
    run_fetch(ds, tmp_path, api)
    differ = diff(ds, tmp_path).split("## ต่างกันจริง")[1].split("## ชื่อใหม่")[0]
    assert "| family | ? |" in differ and "เติมวงศ์" in differ


def test_diff_requires_fetched_file(tmp_path, capsys):
    ds = Dataset(str(tmp_path / "data"))
    ds.write()
    args = ms.build_parser().parse_args(["taxonomy-diff", "--data", ds.root, "--out", str(tmp_path / "o.md")])
    assert ms.cmd_taxonomy_diff(args) == 1
    assert "fetch" in capsys.readouterr().out


def test_diff_marks_unfetched_species(tmp_path, api):
    ds = setup_world(tmp_path, api)
    run_fetch(ds, tmp_path, api, "--only", "escherichia-coli")
    text = diff(ds, tmp_path)
    assert "ยังไม่ได้ดึง 1 ชนิด" in text and "plasmodium-falciparum" in text
