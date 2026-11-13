#!/usr/bin/env python3
"""Microsearch 2.0 — เครื่องมือหลักสำหรับนำเข้าและตรวจข้อมูล

คำสั่ง:
  python scripts/microsearch.py import-seed [--force]
  python scripts/microsearch.py validate [--verbose]
  python scripts/microsearch.py fetch [--refresh] [--only id1,id2] [--sleep 0.34]
  python scripts/microsearch.py taxonomy-diff
  python scripts/microsearch.py build
  python scripts/microsearch.py coverage
  python scripts/microsearch.py images [--only id,..] [--check]

ใช้ไลบรารีมาตรฐานของ Python เท่านั้น (JSON Schema ตรวจด้วยตัวตรวจเล็กๆ ในไฟล์นี้
รองรับเฉพาะคำสำคัญที่ schema/*.json ใช้)
"""

import argparse
import collections
import filecmp
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "seed")
DATA = os.path.join(ROOT, "data")
SCHEMA = os.path.join(ROOT, "schema")
REPORTS = os.path.join(ROOT, "reports")
CACHE = os.path.join(ROOT, "cache")  # คำตอบดิบจาก API (อยู่ใน .gitignore)

GBIF_API = "https://api.gbif.org/v1"
NCBI_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
USER_AGENT = "taxonomy-data-tool/1.0"  # ชื่อกลาง ไม่ใส่ชื่อโปรเจกต์หรือข้อมูลส่วนตัวของผู้ใช้
NCBI_MIN_INTERVAL = 0.34  # NCBI ไม่มี API key: ไม่เกิน 3 คำขอ/วินาที
GBIF_MIN_INTERVAL = 0.1

SLUG_RE = re.compile(r"[^a-z0-9]+")
UNKNOWN = "?"  # ยังไม่ได้จัดวงศ์ ยอมรับได้เฉพาะขั้นวงศ์
UNKNOWN_ALLOWED_RANKS = ("family",)
SHOW_LIMIT = 8  # จำนวนรหัสที่แสดงต่อกลุ่ม warning (ใช้ --verbose เพื่อดูทั้งหมด)


# ---------------------------------------------------------------- JSON / Schema

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_schema(name):
    return load_json(os.path.join(SCHEMA, name))


_TYPE_CHECK = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
}
_TYPE_TH = {"string": "ข้อความ", "integer": "จำนวนเต็ม", "number": "ตัวเลข", "boolean": "จริง/เท็จ",
            "null": "null", "array": "รายการ", "object": "ออบเจ็กต์"}


def schema_errors(value, schema, root=None, path=""):
    """ตรวจค่ากับ JSON Schema (เฉพาะ type, required, properties, additionalProperties,
    enum, items, minItems, minLength, pattern, $ref ภายใน $defs) คืน list ของ (path, ข้อความ)"""
    root = root or schema
    out = []
    if "$ref" in schema:
        node = root
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        return schema_errors(value, node, root, path)
    where = path or "(ทั้งรายการ)"
    types = schema.get("type")
    if types is not None:
        types = [types] if isinstance(types, str) else types
        if not any(_TYPE_CHECK[t](value) for t in types):
            want = " หรือ ".join(_TYPE_TH[t] for t in types)
            return [(where, "ชนิดข้อมูลไม่ถูกต้อง ต้องเป็น%s" % want)]
    if "enum" in schema and value not in schema["enum"]:
        out.append((where, "ค่า %r ไม่อยู่ในที่อนุญาต %s" % (value, schema["enum"])))
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            out.append((where, "ห้ามว่าง"))
        if "pattern" in schema and value and not re.search(schema["pattern"], value):
            out.append((where, "รูปแบบไม่ถูกต้อง %r" % value))
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            out.append((where, "ต้องมีอย่างน้อย %d รายการ" % schema["minItems"]))
        if "items" in schema:
            for i, item in enumerate(value):
                out += schema_errors(item, schema["items"], root, "%s[%d]" % (path, i))
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                out.append(("%s.%s" % (path, key) if path else key, "ขาดช่องที่ต้องมี"))
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for key, sub in value.items():
            sub_path = "%s.%s" % (path, key) if path else key
            if key in props:
                out += schema_errors(sub, props[key], root, sub_path)
            elif extra is False:
                out.append((sub_path, "ช่องนี้ไม่อยู่ใน schema"))
            elif isinstance(extra, dict):
                out += schema_errors(sub, extra, root, sub_path)
    return out


# ---------------------------------------------------------------- ผลตรวจ

class Report:
    """เก็บ error (ห้าม deploy) และ warning (ช่องอังกฤษที่ยังว่าง ฯลฯ)"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, code, file, item_id, msg):
        self.errors.append({"code": code, "file": file, "id": item_id, "msg": msg})

    def warn(self, code, file, item_id, msg):
        self.warnings.append({"code": code, "file": file, "id": item_id, "msg": msg})

    def codes(self, kind="errors"):
        return {x["code"] for x in getattr(self, kind)}


def slugify(scientific_name):
    return SLUG_RE.sub("-", scientific_name.lower()).strip("-")


def rank_key(rank_en):
    """ชื่อขั้นภาษาอังกฤษใน groups.json -> คีย์ใน lineage เช่น 'Major clade' -> 'major_clade'"""
    return re.sub(r"\s+", "_", rank_en.strip().lower())


# ---------------------------------------------------------------- validate

def validate_data(data_dir=DATA, schema_dir=SCHEMA):
    """ตรวจโฟลเดอร์ data ทั้งหมด คืน Report"""
    rep = Report()
    org_schema = load_json(os.path.join(schema_dir, "organism.schema.json"))
    taxon_schema = load_json(os.path.join(schema_dir, "taxon.schema.json"))
    groups_schema = load_json(os.path.join(schema_dir, "groups.schema.json"))

    def read(rel):
        path = os.path.join(data_dir, rel)
        if not os.path.exists(path):
            rep.error("FILE_MISSING", rel, None, "ไม่พบไฟล์")
            return None
        try:
            return load_json(path)
        except (ValueError, OSError) as e:
            rep.error("JSON_INVALID", rel, None, "อ่าน JSON ไม่ได้: %s" % e)
            return None

    groups_doc = read("groups.json")
    taxa = read("taxa.json")

    group_info = {}  # id -> {"ranks": [...], "traits": {...}}
    trait_values, tag_keys = {}, set()
    if groups_doc is not None:
        errs = schema_errors(groups_doc, groups_schema)
        for p, m in errs:
            rep.error("SCHEMA", "groups.json", None, "%s: %s" % (p, m))
        if not errs:
            trait_values = {k: set(v) for k, v in groups_doc["trait_values"].items()}
            tag_keys = {t["key"] for t in groups_doc["tags"]}
            for g in groups_doc["groups"]:
                group_info[g["id"]] = {
                    "ranks": [rank_key(r["en"]) for r in g["ranks"]],
                    "traits": {t["key"] for t in g["traits"]},
                }

    taxa_names = set()
    if taxa is not None:
        if not isinstance(taxa, dict):
            rep.error("SCHEMA", "taxa.json", None, "ต้องเป็นออบเจ็กต์ที่คีย์คือชื่อหน่วยอนุกรมวิธาน")
        else:
            taxa_names = set(taxa)
            for name, t in taxa.items():
                for p, m in schema_errors(t, taxon_schema):
                    rep.error("SCHEMA", "taxa.json", name, "%s: %s" % (p, m))
                # สกุล และชื่อที่ rank เป็น null (ชื่อใหม่ของไฟลัมที่ใช้แสดงคู่กับชื่อตำรา) ไม่ต้องมี about
                if isinstance(t, dict) and t.get("rank") not in ("genus", None):
                    for field in ("about_th", "about_en"):
                        if not (t.get(field) or "").strip():
                            rep.error("TAXON_ABOUT_MISSING", "taxa.json", name,
                                      "ชื่อที่ไม่ใช่สกุล (ขั้น %s) ต้องมี %s" % (t.get("rank"), field))

    seen = {}  # id -> ไฟล์แรกที่พบ
    org_files = sorted(glob.glob(os.path.join(data_dir, "organisms", "*.json")))
    if not org_files:
        rep.error("FILE_MISSING", "organisms/", None, "ไม่พบไฟล์ organisms/*.json")
    for path in org_files:
        rel = "organisms/" + os.path.basename(path)
        stem = os.path.splitext(os.path.basename(path))[0]
        try:
            items = load_json(path)
        except (ValueError, OSError) as e:
            rep.error("JSON_INVALID", rel, None, "อ่าน JSON ไม่ได้: %s" % e)
            continue
        if not isinstance(items, list):
            rep.error("SCHEMA", rel, None, "ต้องเป็นรายการของชนิด")
            continue
        for idx, o in enumerate(items):
            oid = o.get("id") if isinstance(o, dict) else None
            label = oid or "(รายการที่ %d)" % (idx + 1)
            errs = schema_errors(o, org_schema)
            for p, m in errs:
                rep.error("SCHEMA", rel, label, "%s: %s" % (p, m))
            if not isinstance(o, dict):
                continue
            _check_organism(rep, o, rel, label, stem, group_info, trait_values, tag_keys, taxa_names, taxa is not None)
            if oid is not None:
                if oid in seen:
                    rep.error("DUP_ID", rel, oid, "id ซ้ำ (พบแล้วใน %s)" % seen[oid])
                else:
                    seen[oid] = rel
    return rep


def _check_organism(rep, o, rel, label, stem, group_info, trait_values, tag_keys, taxa_names, have_taxa):
    sci = o.get("scientific_name")
    if isinstance(sci, str) and sci and isinstance(o.get("id"), str) and o["id"] != slugify(sci):
        rep.error("ID_MISMATCH", rel, label,
                  "id ไม่ตรงกับชื่อวิทยาศาสตร์ %r (ควรเป็น %r)" % (sci, slugify(sci)))

    gid = o.get("group")
    info = group_info.get(gid) if isinstance(gid, str) else None
    if isinstance(gid, str):
        if group_info and info is None:
            rep.error("GROUP_UNKNOWN", rel, label, "group %r ไม่มีใน groups.json" % gid)
        elif gid != stem:
            rep.error("GROUP_FILE_MISMATCH", rel, label, "group %r ไม่ตรงกับชื่อไฟล์ %s.json" % (gid, stem))

    if isinstance(o.get("reading_th"), str) and not o["reading_th"].strip():
        rep.error("READING_MISSING", rel, label, "ไม่มี reading_th (คำอ่านไทย)")

    # lineage: ลำดับขั้นต้องตรงกับ groups.json > ranks ของกลุ่ม และทุกชื่อต้องมีใน taxa.json
    lineage = o.get("lineage")
    if isinstance(lineage, list) and all(isinstance(x, dict) and isinstance(x.get("rank"), str) for x in lineage):
        got = [x["rank"] for x in lineage]
        if info is not None and got != info["ranks"]:
            missing = [r for r in info["ranks"] if r not in got]
            extra = [r for r in got if r not in info["ranks"]]
            detail = []
            if missing:
                detail.append("ขาดขั้น %s" % ", ".join(missing))
            if extra:
                detail.append("เกินขั้น %s" % ", ".join(extra))
            if not missing and not extra:
                detail.append("ลำดับสลับกัน")
            rep.error("LINEAGE_RANKS", rel, label,
                      "ลำดับชั้นไม่ตรงกับกลุ่ม %s: %s (ต้องเป็น %s)" % (gid, "; ".join(detail), " > ".join(info["ranks"])))
        for x in lineage:
            name = x.get("name")
            if not isinstance(name, str) or not name:
                continue
            if name == UNKNOWN:
                if x["rank"] not in UNKNOWN_ALLOWED_RANKS:
                    rep.error("LINEAGE_UNKNOWN_RANK", rel, label,
                              "ใช้ '?' ได้เฉพาะขั้นวงศ์ แต่พบที่ขั้น %s" % x["rank"])
            elif have_taxa and name not in taxa_names:
                rep.error("LINEAGE_NAME_NOT_IN_TAXA", rel, label,
                          "ชื่อ %r (ขั้น %s) ใน lineage ไม่มีใน taxa.json" % (name, x["rank"]))

    # traits: คีย์ต้องเป็นของกลุ่ม ค่าต้องอยู่ใน groups.json > trait_values
    traits = o.get("traits")
    if isinstance(traits, dict):
        for k, v in traits.items():
            if info is not None and k not in info["traits"]:
                rep.error("TRAIT_KEY", rel, label, "traits.%s ไม่ใช่ลักษณะของกลุ่ม %s" % (k, gid))
            elif k not in trait_values:
                rep.error("TRAIT_KEY", rel, label, "traits.%s ไม่มีใน groups.json > trait_values" % k)
            elif isinstance(v, str) and v not in trait_values[k]:
                rep.error("TRAIT_VALUE", rel, label,
                          "traits.%s = %r ไม่อยู่ในค่าที่อนุญาต %s" % (k, v, sorted(trait_values[k])))

    tags = o.get("tags")
    if isinstance(tags, list) and tag_keys:
        for t in tags:
            if isinstance(t, str) and t not in tag_keys:
                rep.error("TAG_UNKNOWN", rel, label, "tag %r ไม่มีใน groups.json > tags" % t)

    # รูป: license ต้องเป็นหนึ่งใน CC0, CC BY, CC BY-SA, Public domain ที่ระบุชัดเจน
    for i, img in enumerate(o.get("images") or []):
        if isinstance(img, dict) and isinstance(img.get("license"), str) and not ALLOWED_LICENSE_RE.match(img["license"]):
            rep.error("IMAGE_LICENSE", rel, label, "รูปที่ %d: license %r ไม่อยู่ในที่อนุญาต (CC0, CC BY, CC BY-SA, Public domain)" % (i + 1, img["license"]))

    # warning: ช่องอังกฤษที่ยังว่าง
    # name_en เป็นชื่อสามัญภาษาอังกฤษ ชนิดที่ไม่มีชื่อสามัญจริงปล่อยว่างได้ จึงไม่เตือน (coverage นับให้แยกต่างหาก)
    if isinstance(o.get("summary_en"), str) and not o["summary_en"].strip():
        rep.warn("EN_EMPTY_SUMMARY_EN", rel, label, "summary_en ว่าง")
    th, en = o.get("traits_text_th"), o.get("traits_text_en")
    if isinstance(th, dict) and isinstance(en, dict):
        miss = [k for k, v in th.items() if v and not (en.get(k) or "").strip()]
        if miss:
            rep.warn("EN_EMPTY_TRAITS_TEXT_EN", rel, label, "traits_text_en ยังว่าง: %s" % ", ".join(miss))
    if "extra_th" in o and "extra_en" not in o:
        rep.warn("EN_EMPTY_EXTRA_EN", rel, label, "มี extra_th แต่ไม่มี extra_en")


WARN_TITLES = {
    "EN_EMPTY_SUMMARY_EN": "summary_en ยังว่าง",
    "EN_EMPTY_TRAITS_TEXT_EN": "traits_text_en ยังว่างบางคีย์",
    "EN_EMPTY_EXTRA_EN": "มี extra_th แต่ไม่มี extra_en",
}


def print_report(rep, verbose=False):
    for e in rep.errors:
        where = e["file"] + (" [%s]" % e["id"] if e["id"] else "")
        print("ข้อผิดพลาด: %s — %s" % (where, e["msg"]))
    groups = {}
    for w in rep.warnings:
        groups.setdefault(w["code"], []).append(w)
    for code, ws in groups.items():
        ids = [w["id"] for w in ws]
        shown = ids if verbose else ids[:SHOW_LIMIT]
        more = "" if len(shown) == len(ids) else " ... (อีก %d, ใช้ --verbose ดูทั้งหมด)" % (len(ids) - len(shown))
        print("คำเตือน: %s %d รายการ: %s%s" % (WARN_TITLES.get(code, code), len(ws), ", ".join(map(str, shown)), more))
    print("สรุป: %d ข้อผิดพลาด, %d คำเตือน" % (len(rep.errors), len(rep.warnings)))
    if rep.errors:
        print("ไม่ผ่าน: ห้าม deploy จนกว่าจะแก้ข้อผิดพลาด")
    else:
        print("ผ่าน: ไม่มีข้อผิดพลาด")


def cmd_validate(args):
    rep = validate_data(args.data)
    print_report(rep, args.verbose)
    return 1 if rep.errors else 0


# ---------------------------------------------------------------- import-seed

def seed_files(seed_dir):
    files = ["taxa.json", "groups.json"]
    files += ["organisms/" + os.path.basename(p) for p in sorted(glob.glob(os.path.join(seed_dir, "organisms", "*.json")))]
    return files


def cmd_import_seed(args, ask=None):
    """คัดลอก seed -> data แบบไบต์ต่อไบต์ ไม่ทับไฟล์ที่แก้แล้ว ยกเว้น --force หรือผู้ใช้ตอบ y"""
    if not os.path.isdir(args.seed):
        print("ไม่พบโฟลเดอร์ seed: %s" % args.seed)
        return 1
    if ask is None:
        ask = _ask_overwrite if sys.stdin.isatty() else (lambda rel: False)
    copied, same, skipped = [], [], []
    missing = [r for r in ("taxa.json", "groups.json") if not os.path.exists(os.path.join(args.seed, r))]
    if missing:
        print("seed ไม่ครบ ขาด: %s" % ", ".join(missing))
        return 1
    for rel in seed_files(args.seed):
        src, dst = os.path.join(args.seed, rel), os.path.join(args.data, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)
            copied.append(rel)
        elif filecmp.cmp(src, dst, shallow=False):
            same.append(rel)
        elif args.force or ask(rel):
            shutil.copyfile(src, dst)
            copied.append(rel + " (ทับไฟล์ที่ต่างจาก seed)")
        else:
            skipped.append(rel)
    for r in copied:
        print("คัดลอก: %s" % r)
    for r in skipped:
        print("ข้าม: %s (ต่างจาก seed คงไฟล์ใน data/ ไว้ ใช้ --force เพื่อทับ)" % r)
    print("สรุป: คัดลอก %d, เหมือน seed อยู่แล้ว %d, ข้าม %d" % (len(copied), len(same), len(skipped)))
    return 0


def _ask_overwrite(rel):
    try:
        ans = input("data/%s ต่างจาก seed (อาจแก้แล้ว) ทับด้วย seed ไหม? [y/N] " % rel)
    except EOFError:
        return False
    return ans.strip().lower() in ("y", "yes", "ใช่")


# ---------------------------------------------------------------- fetch (GBIF + NCBI)

class FetchError(Exception):
    pass


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def http_get_bytes(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


class Fetcher:
    """ดึง URL พร้อม cache คำตอบดิบ (ไฟล์ละคำขอ) และหน่วงเวลาต่อแหล่ง ไม่ให้เกินอัตราที่กำหนด
    คำตอบที่ผิดพลาดไม่ถูก cache (รันซ้ำจะลองใหม่)"""

    def __init__(self, cache_dir=CACHE, refresh=False, getter=None, intervals=None, retries=3, bytes_getter=None):
        self.cache_dir = cache_dir
        self.refresh = refresh
        self.getter = getter or http_get
        self.bytes_getter = bytes_getter
        self.intervals = intervals if intervals is not None else {"ncbi": NCBI_MIN_INTERVAL, "gbif": GBIF_MIN_INTERVAL}
        self.retries = retries
        self.stats = {"api": 0, "cache": 0}
        self._last = {}

    def cache_path(self, source, label, url, ext):
        slug = re.sub(r"[^A-Za-z0-9]+", "-", label).strip("-")[:60] or "q"
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
        return os.path.join(self.cache_dir, source, "%s-%s.%s" % (slug, digest, ext))

    def get(self, source, label, url, ext="json"):
        path = self.cache_path(source, label, url, ext)
        if not self.refresh and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.stats["cache"] += 1
                return f.read()
        body = self._request(source, url)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(body)
        os.replace(tmp, path)
        return body

    def get_bytes(self, source, label, url):
        """ดาวน์โหลดไฟล์ไบนารี (รูป) พร้อม cache แบบเดียวกับ get()"""
        path = self.cache_path(source, label, url, "bin")
        if not self.refresh and os.path.exists(path):
            with open(path, "rb") as f:
                self.stats["cache"] += 1
                return f.read()
        body = self._request(source, url, binary=True)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(body)
        os.replace(tmp, path)
        return body

    def _request(self, source, url, binary=False):
        last_err = None
        for attempt in range(1, self.retries + 1):
            wait = self.intervals.get(source, 0) - (time.monotonic() - self._last.get(source, -1e9))
            if wait > 0:
                time.sleep(wait)
            self._last[source] = time.monotonic()
            self.stats["api"] += 1
            try:
                return (self.bytes_getter or http_get_bytes)(url) if binary else self.getter(url)
            except urllib.error.HTTPError as e:
                last_err = "HTTP %s" % e.code
                if e.code not in (429, 500, 502, 503, 504):
                    break
                if e.code == 429:  # เซิร์ฟเวอร์ขอให้ช้าลง: รอตามที่บอก (สูงสุด 90 วินาที)
                    try:
                        delay = int((e.headers or {}).get("Retry-After", 20))
                    except (TypeError, ValueError):
                        delay = 20
                    time.sleep(min(max(delay, 5), 90) if self.intervals else 0)
                    continue
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_err = str(e)
            time.sleep(min(2 * attempt, 6) if self.intervals else 0)
        raise FetchError("%s: %s" % (url, last_err))


GBIF_RANKS = ("kingdom", "phylum", "class", "order", "family", "genus")
NCBI_INFORMAL = ("no rank", "clade", "cellular root", "acellular root")


def fetch_gbif(fx, name):
    """GBIF species/match: ใช้เฉพาะ matchType=EXACT ระดับ SPECIES นอกนั้น key เป็น null (ไม่เดา)"""
    entry = {"key": None, "match_type": None, "status": None, "accepted_key": None, "accepted_name": None,
             "synonyms": [], "lineage": {}, "note": ""}
    url = GBIF_API + "/species/match?" + urllib.parse.urlencode({"name": name, "verbose": "false"})
    m = json.loads(fx.get("gbif", "match-" + name, url))
    entry["match_type"] = m.get("matchType")
    if m.get("matchType") != "EXACT":
        entry["note"] = "GBIF matchType=%s จึงไม่ใช้ผล (ไม่เดา)" % m.get("matchType")
        return entry
    if m.get("rank") != "SPECIES":
        entry["note"] = "GBIF จับคู่ได้ที่ขั้น %s ไม่ใช่ชนิด จึงไม่ใช้ผล" % m.get("rank")
        return entry
    entry["key"] = m["usageKey"]
    entry["status"] = m.get("status")
    if m.get("status") not in ("ACCEPTED", "SYNONYM"):
        entry["note"] = "GBIF status=%s" % m.get("status")
    entry["lineage"] = {r: m[r] for r in GBIF_RANKS if m.get(r)}
    if m.get("status") == "ACCEPTED":
        entry["accepted_key"] = m["usageKey"]
        entry["accepted_name"] = m.get("canonicalName")
    elif m.get("acceptedUsageKey"):
        entry["accepted_key"] = m["acceptedUsageKey"]
        acc = json.loads(fx.get("gbif", "species-%s" % m["acceptedUsageKey"],
                                "%s/species/%s" % (GBIF_API, m["acceptedUsageKey"])))
        entry["accepted_name"] = acc.get("canonicalName")
    if entry["accepted_key"]:
        url = "%s/species/%s/synonyms?limit=100" % (GBIF_API, entry["accepted_key"])
        syn = json.loads(fx.get("gbif", "synonyms-%s" % entry["accepted_key"], url))
        names = {s.get("canonicalName") for s in syn.get("results", []) if s.get("canonicalName")}
        names.discard(entry["accepted_name"])
        entry["synonyms"] = sorted(names)
    return entry


def parse_ncbi_taxon(xml_text):
    root = ET.fromstring(xml_text)
    tax = root.find("Taxon")
    if tax is None:
        return None
    other = tax.find("OtherNames")
    syn = sorted({e.text for e in (other if other is not None else []) if e.tag in ("Synonym", "GenbankSynonym") and e.text})
    lineage = []
    for t in tax.findall("./LineageEx/Taxon"):
        rank = (t.findtext("Rank") or "").strip()
        lineage.append({"rank": "domain" if rank == "superkingdom" else rank,
                        "name": (t.findtext("ScientificName") or "").strip(),
                        "taxid": int(t.findtext("TaxId") or 0)})
    return {"taxid": int(tax.findtext("TaxId")), "name": (tax.findtext("ScientificName") or "").strip(),
            "rank": (tax.findtext("Rank") or "").strip(), "synonyms": syn, "lineage": lineage}


def fetch_ncbi(fx, name):
    """NCBI taxonomy: esearch [All Names] ต้องได้ taxid เดียวและเป็นขั้น species จึงจะใช้ (ไม่เดา)"""
    entry = {"taxid": None, "accepted_name": None, "rank": None, "synonyms": [], "lineage": [], "note": ""}
    term = '"%s"[All Names]' % name
    url = NCBI_API + "/esearch.fcgi?" + urllib.parse.urlencode({"db": "taxonomy", "term": term, "retmode": "json"})
    res = json.loads(fx.get("ncbi", "esearch-" + name, url)).get("esearchresult", {})
    ids = res.get("idlist", [])
    if not ids:
        entry["note"] = "NCBI ไม่พบชื่อนี้"
        return entry
    if len(ids) > 1:
        entry["note"] = "NCBI พบหลาย taxid (%s) จึงไม่ใช้ผล (ไม่เดา)" % ", ".join(ids)
        return entry
    url = NCBI_API + "/efetch.fcgi?" + urllib.parse.urlencode({"db": "taxonomy", "id": ids[0], "retmode": "xml"})
    tax = parse_ncbi_taxon(fx.get("ncbi", "efetch-" + ids[0], url, "xml"))
    if tax is None:
        entry["note"] = "NCBI efetch ไม่คืนข้อมูล taxid %s" % ids[0]
        return entry
    if tax["rank"] != "species":
        entry["note"] = "NCBI taxid %s เป็นขั้น %s ไม่ใช่ species จึงไม่ใช้ผล" % (tax["taxid"], tax["rank"])
        return entry
    entry.update({"taxid": tax["taxid"], "accepted_name": tax["name"], "rank": tax["rank"],
                  "synonyms": tax["synonyms"], "lineage": tax["lineage"]})
    if tax["name"] != name:
        entry["note"] = "ชื่อที่ยอมรับของ NCBI ต่างจากชื่อที่ค้น (%s)" % tax["name"]
    return entry


def load_organisms(data_dir):
    out = []
    for path in sorted(glob.glob(os.path.join(data_dir, "organisms", "*.json"))):
        out.extend(load_json(path))
    return out


def fetched_path(data_dir):
    return os.path.join(data_dir, "generated", "taxa-fetched.json")


def cmd_fetch(args, fetcher=None):
    """ดึง GBIF + NCBI ต่อชนิด เขียน data/generated/taxa-fetched.json (ไม่แตะ data/organisms)"""
    orgs = load_organisms(args.data)
    if args.only:
        wanted = [x.strip() for x in args.only.split(",") if x.strip()]
        unknown = [w for w in wanted if w not in {o["id"] for o in orgs}]
        if unknown:
            print("ไม่พบ id: %s" % ", ".join(unknown))
            return 1
        todo = [o for o in orgs if o["id"] in wanted]
    else:
        todo = orgs
    fx = fetcher or Fetcher(args.cache, args.refresh)
    out_path = fetched_path(args.data)
    result = {}
    if os.path.exists(out_path):
        result = load_json(out_path).get("organisms", {})
    failures = []
    for i, o in enumerate(todo, 1):
        entry = {"scientific_name": o["scientific_name"]}
        for src, fn in (("gbif", fetch_gbif), ("ncbi", fetch_ncbi)):
            try:
                entry[src] = fn(fx, o["scientific_name"])
            except (FetchError, ValueError, ET.ParseError) as e:
                failures.append((o["id"], src, str(e)))
                entry[src] = None  # ไม่รู้ผล (ต่างจาก "ไม่พบ") รันซ้ำจะลองใหม่
        g, n = entry["gbif"], entry["ncbi"]
        print("[%d/%d] %s  GBIF=%s NCBI=%s" % (
            i, len(todo), o["id"],
            ("ดึงไม่ได้" if g is None else g["key"] if g["key"] else "null (%s)" % g["match_type"]),
            ("ดึงไม่ได้" if n is None else n["taxid"] if n["taxid"] else "null")))
        result[o["id"]] = entry
    ordered = {o["id"]: result[o["id"]] for o in orgs if o["id"] in result}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"_about": "ผลดึงจาก GBIF species/match และ NCBI taxonomy (ดิบ ยังไม่ตัดสิน) ห้ามแก้เอง สร้างจาก microsearch.py fetch",
                   "organisms": ordered}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("สรุป: %d ชนิด, เรียก API %d ครั้ง, ใช้ cache %d ครั้ง" % (len(todo), fx.stats["api"], fx.stats["cache"]))
    for oid, src, msg in failures:
        print("ดึงไม่สำเร็จ: %s (%s) %s" % (oid, src, msg))
    if failures:
        print("มี %d รายการดึงไม่สำเร็จ รันซ้ำเพื่อลองใหม่ (รายการที่สำเร็จแล้วใช้ cache)" % len(failures))
        return 1
    return 0


# ---------------------------------------------------------------- taxonomy-diff

# ชื่อที่เป็นของเดียวกันตามธรรมเนียมการเรียก ไม่นับเป็นความต่าง (ไม่แสดงในรายงาน)
EQUIV_NAMES = (("Eukarya", "Eukaryota"), ("Plantae", "Viridiplantae"), ("Animalia", "Metazoa"))
SKIP_RANKS = ("supergroup",)  # ซูเปอร์กรุ๊ปของโพรทิสต์เขียนเองใน groups.json ไม่มีใน API
CATEGORY_ORDER = ("differ", "renamed", "notfound", "match")
CATEGORY_TITLES = {
    "differ": "ต่างกันจริง",
    "renamed": "ชื่อใหม่ของชื่อเดียวกัน",
    "notfound": "หาไม่เจอ",
    "match": "ตรงกันหมด",
}
STATUS_RANK = {"differ": 3, "renamed": 2, "match": 1}


def build_alias(groups_doc):
    """คืน (equiv, renamed, textbook): equiv = ชื่อเทียบเท่า, renamed = ชื่อตำรา<->ชื่อใหม่ใน groups.json,
    textbook = ชื่อตำราที่ตั้งใจใช้คู่กับชื่อใหม่"""
    equiv, renamed, textbook = {}, {}, set()
    for a, b in EQUIV_NAMES:
        equiv.setdefault(a, set()).add(b)
        equiv.setdefault(b, set()).add(a)
    for g in groups_doc["groups"]:
        for p in g.get("phyla") or []:
            if p.get("new_name"):
                renamed.setdefault(p["name"], set()).add(p["new_name"])
                renamed.setdefault(p["new_name"], set()).add(p["name"])
                textbook.add(p["name"])
    return equiv, renamed, textbook


def gbif_view(entry):
    if not entry or entry.get("key") is None:
        return None
    return {"formal": dict(entry["lineage"]), "all": set(entry["lineage"].values()),
            "accepted": entry.get("accepted_name"), "synonyms": set(entry.get("synonyms", []))}


def ncbi_view(entry):
    if not entry or entry.get("taxid") is None:
        return None
    formal, allnames = {}, set()
    for t in entry["lineage"]:
        allnames.add(t["name"])
        if t["rank"] not in NCBI_INFORMAL:
            formal.setdefault(t["rank"], t["name"])
    return {"formal": formal, "all": allnames, "accepted": entry.get("accepted_name"),
            "synonyms": set(entry.get("synonyms", []))}


def compare_cell(rank, ours, view, alias):
    """เทียบชื่อหนึ่งขั้นกับหนึ่งแหล่ง คืน (สถานะ, ชื่อจาก API)
    สถานะ: match | renamed | differ | none (แหล่งนั้นไม่มีข้อมูลให้เทียบ)"""
    equiv, renamed, _ = alias
    if view is None:
        return "none", None
    api = view["formal"].get(rank)
    if ours == UNKNOWN:
        return ("differ", api) if api else ("none", None)
    if api:
        if api == ours or api in equiv.get(ours, ()):
            return "match", api
        if api in renamed.get(ours, ()):
            return "renamed", api
        return "differ", api
    # API ไม่มีขั้นนี้ (เช่น ซูเปอร์กรุ๊ป กลุ่มย่อยของโพรทิสต์ หรือ NCBI ที่เป็น no rank): ดูว่ามีชื่อนี้ที่ใดในลำดับชั้น
    if ours in view["all"] or any(v in view["all"] for v in equiv.get(ours, ())):
        return "match", ours
    if any(v in view["all"] for v in renamed.get(ours, ())):
        return "renamed", next(v for v in renamed[ours] if v in view["all"])
    return "none", None


def combine_status(gs, ns):
    sts = [s for s in (gs, ns) if s != "none"]
    return max(sts, key=lambda s: STATUS_RANK[s]) if sts else "nodata"


def propose(rank, ours, status, gs, gname, ns, nname, textbook):
    if status == "renamed":
        names = sorted({n for s, n in ((gs, gname), (ns, nname)) if s == "renamed" and n})
        if rank == "species":
            return "ชื่อที่ยอมรับตอนนี้คือ %s (เสนอ: ตัดสินในเฟส 5)" % " / ".join(names)
        if ours in textbook:
            return "คงชื่อตำรา %s แสดงชื่อใหม่ %s คู่กัน (ตามที่ตั้งใจ)" % (ours, " / ".join(names))
        return "ชื่อเปลี่ยนเป็น %s (เสนอ: ตัดสินในเฟส 5)" % " / ".join(names)
    differing = {n for s, n in ((gs, gname), (ns, nname)) if s == "differ"}
    if ours == UNKNOWN:
        return "เติมวงศ์: GBIF=%s NCBI=%s (ตรวจเองก่อน)" % (gname or "—", nname or "—")
    others_match = any(s in ("match", "renamed") for s in (gs, ns))
    if len(differing) == 1 and not others_match and gs == "differ" and ns == "differ":
        return "เสนอเปลี่ยนเป็น %s (GBIF และ NCBI ตรงกัน)" % next(iter(differing))
    if gs == "differ" and ns == "differ":
        return "ตรวจเอง (GBIF กับ NCBI ไม่ตรงกัน)"
    only = "GBIF" if gs == "differ" else "NCBI"
    if others_match:
        return "ตรวจเอง (%s ต่าง อีกแหล่งตรงกับเรา)" % only
    return "ตรวจเอง (มีแหล่งเดียว: %s)" % only


def compare_organism(o, group_ranks, fetched, alias):
    """คืน (หมวด, แถวที่ไม่ตรง, หมายเหตุ) ของหนึ่งชนิด"""
    _, _, textbook = alias
    gv, nv = gbif_view(fetched.get("gbif")), ncbi_view(fetched.get("ncbi"))
    if gv is None and nv is None:
        return "notfound", [], ""
    cells = []  # (rank, ours, gs, gname, ns, nname)
    ours_by_rank = {x["rank"]: x["name"] for x in o["lineage"]}
    for rank in group_ranks:
        if rank in SKIP_RANKS or rank not in ours_by_rank:
            continue
        ours = ours_by_rank[rank]
        gs, gname = compare_cell(rank, ours, gv, alias)
        ns, nname = compare_cell(rank, ours, nv, alias)
        cells.append([rank, ours, gs, gname, ns, nname])
    # ชนิด: เทียบชื่อวิทยาศาสตร์กับชื่อที่ยอมรับ
    sp = ["species", o["scientific_name"], "none", None, "none", None]
    for idx, view in ((2, gv), (4, nv)):
        if view is None:
            continue
        acc = view["accepted"]
        if acc is None:  # เช่น GBIF status=DOUBTFUL ไม่มีชื่อที่ยอมรับ เทียบชื่อชนิดไม่ได้ (ลำดับชั้นยังเทียบได้)
            continue
        if acc == o["scientific_name"]:
            sp[idx], sp[idx + 1] = "match", acc
        else:
            # ทั้ง GBIF (EXACT) และ NCBI ([All Names]) จับคู่ด้วยชื่อของเรา ถ้าชื่อที่ยอมรับต่างไป
            # แปลว่าชื่อของเราเป็นชื่อพ้อง = ชื่อใหม่ของสิ่งมีชีวิตเดียวกัน
            sp[idx], sp[idx + 1] = "renamed", acc
    # ชนิดถูกเปลี่ยนชื่อ => สกุลที่ต่างเพราะย้ายสกุลก็เป็น "ชื่อใหม่" ไม่ใช่ความต่างจริง
    for idx, view in ((2, gv), (4, nv)):
        if view is not None and sp[idx] == "renamed" and view["accepted"]:
            new_genus = view["accepted"].split()[0]
            for c in cells:
                if c[0] == "genus" and c[idx] == "differ" and c[idx + 1] == new_genus:
                    c[idx] = "renamed"
    cells.append(sp)
    rows, nodata = [], []
    for rank, ours, gs, gname, ns, nname in cells:
        st = combine_status(gs, ns)
        if st == "nodata":
            nodata.append(rank)
        elif st in ("differ", "renamed"):
            rows.append({"rank": rank, "ours": ours, "gbif": gname if gs != "none" else None,
                         "ncbi": nname if ns != "none" else None, "status": st,
                         "proposal": propose(rank, ours, st, gs, gname, ns, nname, textbook)})
    notes = []
    if gv is None:
        notes.append("ไม่พบใน GBIF")
    if nv is None:
        notes.append("ไม่พบใน NCBI")
    for label, entry in (("GBIF", fetched.get("gbif")), ("NCBI", fetched.get("ncbi"))):
        if entry and entry.get("status") == "DOUBTFUL":
            notes.append("%s status=DOUBTFUL (ไม่มีชื่อที่ยอมรับ)" % label)
    if nodata:
        notes.append("เทียบไม่ได้: " + ", ".join(nodata))
    category = "differ" if any(r["status"] == "differ" for r in rows) else "renamed" if rows else "match"
    return category, rows, "; ".join(notes)


def _cell(text):
    return ("—" if text is None else str(text)).replace("|", "\\|").replace("\n", " ")


def build_taxonomy_report(data_dir):
    groups_doc = load_json(os.path.join(data_dir, "groups.json"))
    fetched = load_json(fetched_path(data_dir))["organisms"]
    alias = build_alias(groups_doc)
    ranks = {g["id"]: [rank_key(r["en"]) for r in g["ranks"]] for g in groups_doc["groups"]}
    orgs = load_organisms(data_dir)
    buckets = {c: [] for c in CATEGORY_ORDER}
    pending = []
    for o in orgs:
        if o["id"] not in fetched:
            pending.append(o)
            continue
        cat, rows, note = compare_organism(o, ranks[o["group"]], fetched[o["id"]], alias)
        buckets[cat].append((o, rows, note, fetched[o["id"]]))

    def name(o):
        return "*%s* (%s)" % (o["scientific_name"], o["group"])

    L = ["# รายงานเทียบลำดับชั้นกับ GBIF และ NCBI", "",
         "สร้างจาก `python scripts/microsearch.py taxonomy-diff` (ข้อมูลดิบ `data/generated/taxa-fetched.json`)",
         "รายงานนี้ **ไม่แก้ข้อมูลอัตโนมัติ** ผู้ใช้ตัดสินก่อนแก้ในเฟส 5", "", "## สรุป", "",
         "| หมวด | จำนวนชนิด |", "| --- | --- |"]
    for c in CATEGORY_ORDER:
        L.append("| %s | %d |" % (CATEGORY_TITLES[c], len(buckets[c])))
    L.append("| รวม | %d จาก %d |" % (sum(len(v) for v in buckets.values()), len(orgs)))
    if pending:
        L += ["", "> ยังไม่ได้ดึง %d ชนิด (ไม่อยู่ในรายงาน): %s" % (len(pending), ", ".join(o["id"] for o in pending))]
    one_src = [o["id"] for c in buckets for (o, _, note, _) in buckets[c] if "ไม่พบใน" in note]
    L += ["", "วิธีเทียบ:",
          "- เทียบชื่อของเราทีละขั้นกับชื่อที่ API ให้ในขั้นเดียวกัน ถ้า API ไม่มีขั้นนั้น (เช่น NCBI ใช้ no rank) "
          "ดูว่ามีชื่อของเราอยู่ที่ใดในลำดับชั้นของ API หรือไม่ ถ้าไม่มีเลยถือว่าเทียบไม่ได้ ไม่นับเป็นความต่าง",
          "- ซูเปอร์กรุ๊ปของโพรทิสต์ไม่เทียบ (ไม่มีใน API) เทียบเฉพาะกลุ่มหลัก กลุ่มย่อย และสกุล",
          "- ชื่อที่นับว่าเป็นของเดียวกันตามธรรมเนียม ไม่ถือเป็นความต่าง: "
          + ", ".join("%s = %s" % p for p in EQUIV_NAMES),
          "- ชื่อไฟลัมตามตำราที่ตั้งใจใช้คู่กับชื่อใหม่ใน `groups.json` จัดเป็น \"ชื่อใหม่ของชื่อเดียวกัน\" ไม่ใช่ความต่างจริง",
          "- ชนิดที่ GBIF/NCBI ไม่พบ (หรือเป็น FUZZY/HIGHERRANK) ใช้ id เป็น null ไม่เดา",
          "- ชนิดที่พบแหล่งเดียว (%d ชนิด) เทียบกับแหล่งที่พบ: %s" % (len(one_src), ", ".join(one_src) or "—"), ""]

    head = ["| ชนิด | ลำดับขั้น | ของเรา | GBIF | NCBI | ข้อเสนอ |", "| --- | --- | --- | --- | --- | --- |"]
    for c in ("differ", "renamed"):
        L += ["## %s (%d ชนิด)" % (CATEGORY_TITLES[c], len(buckets[c])), ""]
        if buckets[c]:
            L += head
            for o, rows, note, _ in buckets[c]:
                for r in rows:
                    L.append("| %s | %s | %s | %s | %s | %s |" % (name(o), r["rank"], _cell(r["ours"]), _cell(r["gbif"]),
                                                                  _cell(r["ncbi"]), _cell(r["proposal"])))
        L.append("")
    L += ["## %s (%d ชนิด)" % (CATEGORY_TITLES["notfound"], len(buckets["notfound"])), ""]
    if buckets["notfound"]:
        L += head
        for o, _, _, f in buckets["notfound"]:
            L.append("| %s | ชนิด | %s | %s | %s | ไม่แก้ ตรวจชื่อเอง |" % (
                name(o), _cell(o["scientific_name"]), _cell((f.get("gbif") or {}).get("note") or "ดึงไม่ได้"),
                _cell((f.get("ncbi") or {}).get("note") or "ดึงไม่ได้")))
    L += ["", "## %s (%d ชนิด)" % (CATEGORY_TITLES["match"], len(buckets["match"])), ""]
    if buckets["match"]:
        L += ["| ชนิด | หมายเหตุ |", "| --- | --- |"]
        for o, _, note, _ in buckets["match"]:
            L.append("| %s | %s |" % (name(o), _cell(note or None)))
    L.append("")
    return "\n".join(L), {c: len(v) for c, v in buckets.items()}, len(pending)


def cmd_taxonomy_diff(args):
    if not os.path.exists(fetched_path(args.data)):
        print("ไม่พบ %s ให้รัน fetch ก่อน" % fetched_path(args.data))
        return 1
    text, counts, pending = build_taxonomy_report(args.data)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("เขียน %s" % args.out)
    for c in CATEGORY_ORDER:
        print("  %s: %d ชนิด" % (CATEGORY_TITLES[c], counts[c]))
    if pending:
        print("  ยังไม่ได้ดึง: %d ชนิด" % pending)
    return 0


# ---------------------------------------------------------------- coverage

def coverage_data(data_dir=DATA):
    """นับช่องภาษาอังกฤษที่ยังว่างต่อกลุ่ม คืน (แถวต่อกลุ่ม, รายการช่องว่างต่อชนิด)"""
    groups_doc = load_json(os.path.join(data_dir, "groups.json"))
    taxa = load_json(os.path.join(data_dir, "taxa.json"))
    rows = []
    gaps = {}
    for g in groups_doc["groups"]:
        orgs = [o for o in load_organisms(data_dir) if o["group"] == g["id"]]
        r = {"id": g["id"], "species": len(orgs), "summary_en": 0, "traits_text_en": 0, "traits_text_total": 0,
             "extra_en": 0, "name_en_empty": 0, "taxa_about_en": 0}
        for o in orgs:
            miss = []
            if not (o.get("summary_en") or "").strip():
                r["summary_en"] += 1
                miss.append("summary_en")
            th, en = o.get("traits_text_th") or {}, o.get("traits_text_en") or {}
            for k, v in th.items():
                if v:
                    r["traits_text_total"] += 1
                    if not (en.get(k) or "").strip():
                        r["traits_text_en"] += 1
                        miss.append("traits_text_en." + k)
            if "extra_th" in o and not o.get("extra_en"):
                r["extra_en"] += 1
                miss.append("extra_en")
            if not (o.get("name_en") or "").strip():
                r["name_en_empty"] += 1
            if miss:
                gaps[o["id"]] = miss
        used = {x["name"] for o in orgs for x in o["lineage"]} - {UNKNOWN}
        r["taxa_about_en"] = sum(1 for n in used if taxa.get(n, {}).get("rank") not in ("genus", None) and not (taxa[n].get("about_en") or "").strip())
        r["gaps"] = r["summary_en"] + r["traits_text_en"] + r["extra_en"]
        rows.append(r)
    return rows, gaps


def build_coverage_report(data_dir=DATA):
    rows, gaps = coverage_data(data_dir)
    L = ["# ความครบของภาษาอังกฤษ", "",
         "สร้างจาก `python scripts/microsearch.py coverage` นับช่องที่ **ยังว่าง** ต่อกลุ่ม (0 = ครบ)", "",
         "| กลุ่ม | ชนิด | summary_en ว่าง | traits_text_en ว่าง (จากทั้งหมด) | extra_en ว่าง | รวมช่องว่าง | name_en ว่าง (ไม่มีชื่อสามัญ ว่างได้) | about_en ของชื่อในแผนผังว่าง |",
         "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    tot = Counter()
    for r in rows:
        L.append("| %s | %d | %d | %d / %d | %d | %d | %d | %d |" % (r["id"], r["species"], r["summary_en"], r["traits_text_en"], r["traits_text_total"],
                                                                  r["extra_en"], r["gaps"], r["name_en_empty"], r["taxa_about_en"]))
        for k in ("species", "summary_en", "traits_text_en", "traits_text_total", "extra_en", "gaps", "name_en_empty", "taxa_about_en"):
            tot[k] += r[k]
    L.append("| **รวม** | %d | %d | %d / %d | %d | %d | %d | %d |" % (tot["species"], tot["summary_en"], tot["traits_text_en"], tot["traits_text_total"],
                                                                      tot["extra_en"], tot["gaps"], tot["name_en_empty"], tot["taxa_about_en"]))
    L += ["", "`name_en` ว่างได้เมื่อไม่มีชื่อสามัญภาษาอังกฤษจริง (ห้ามแต่งชื่อ) ส่วน about_en ของสกุลว่างได้ตามกติกา validate", ""]
    if gaps:
        L += ["## ชนิดที่ยังมีช่องว่าง", ""]
        for oid, miss in gaps.items():
            L.append("- `%s`: %s" % (oid, ", ".join(miss)))
        L.append("")
    return "\n".join(L), tot


def cmd_coverage(args):
    text, tot = build_coverage_report(args.data)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    rows, _ = coverage_data(args.data)
    print("เขียน %s" % args.out)
    for r in rows:
        print("  %-9s ชนิด %3d  ช่องว่าง %3d (summary_en %d, traits_text_en %d, extra_en %d)  name_en ว่าง %d" % (
            r["id"], r["species"], r["gaps"], r["summary_en"], r["traits_text_en"], r["extra_en"], r["name_en_empty"]))
    print("รวมช่องอังกฤษที่ยังว่าง: %d" % tot["gaps"])
    return 0


# ---------------------------------------------------------------- build

SITE_DATA = os.path.join(ROOT, "site", "data")
ILLUSTRATIONS = os.path.join(SEED, "illustrations.json")  # ภาพวาดชั่วคราวจนกว่าจะมีรูปจริง (เฟส 6)


class BuildError(Exception):
    pass


def write_min_json(path, obj):
    """JSON ย่อขนาด (ไม่มีช่องว่าง, UTF-8 ตรงๆ) ลงท้ายด้วยขึ้นบรรทัดใหม่"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"), sort_keys=False)
        f.write("\n")


SYNONYM_LIMIT = 12  # ต่อแหล่ง (NCBI บางชนิดมีชื่อพ้องเป็นสิบ)


def load_synonyms(data_dir):
    """ชื่อพ้องและชื่อที่ยอมรับตอนนี้ จาก data/generated/taxa-fetched.json (ถ้ามี) สำหรับใช้ค้นหา
    คืน {id: [ชื่อ ...]} ไม่รวมชื่อวิทยาศาสตร์ของเราเอง เรียงลำดับคงที่"""
    path = fetched_path(data_dir)
    if not os.path.exists(path):
        return {}
    own = {o["id"]: o["scientific_name"] for o in load_organisms(data_dir)}
    out = {}
    for oid, entry in load_json(path).get("organisms", {}).items():
        if oid not in own:
            continue
        names = []
        for src in ("gbif", "ncbi"):
            e = entry.get(src)
            if not e:
                continue
            if e.get("accepted_name"):
                names.append(e["accepted_name"])
            names += e.get("synonyms", [])[:SYNONYM_LIMIT]
        seen, uniq = set(), []
        for n in names:
            if n != own[oid] and n.lower() not in seen:
                seen.add(n.lower())
                uniq.append(n)
        if uniq:
            out[oid] = uniq
    return out


def build_site_data(data_dir, illustrations_path):
    """คืน {ชื่อไฟล์: ข้อมูล} ที่จะเขียนไป site/data/ (ยังไม่เขียนไฟล์ใด) ถ้าข้อมูลไม่ครบจะ raise BuildError"""
    groups_doc = load_json(os.path.join(data_dir, "groups.json"))
    taxa = load_json(os.path.join(data_dir, "taxa.json"))
    orgs = load_organisms(data_dir)
    gmap = {g["id"]: g for g in groups_doc["groups"]}
    tags_by_key = {t["key"]: t for t in groups_doc["tags"]}
    readings = {n: t.get("reading_th", "") for n, t in taxa.items()}

    files = {}
    meta_groups = groups_doc["groups"]
    phyla_names = {n for g in groups_doc["groups"] for p in g.get("phyla") or [] for n in (p["name"], p.get("new_name")) if n}
    files["meta.json"] = {
        "groups": meta_groups,
        "trait_values": groups_doc["trait_values"],
        "filter_en": groups_doc.get("filter_en", {}),
        "tags": groups_doc["tags"],
        "levels": groups_doc["levels"],
        "readings": {n: readings[n] for n in sorted(phyla_names) if readings.get(n)},
    }

    synonyms = load_synonyms(data_dir)
    index, per_group, credits = [], {gid: [] for gid in gmap}, []
    for o in orgs:
        g = gmap[o["group"]]
        names = [x["name"] for x in o["lineage"]]
        phyla = g.get("phyla") or []
        p_idx = next((i for i, p in enumerate(phyla) if p["name"] in names), None)
        if p_idx is None:
            raise BuildError("ชนิด %s: ไม่พบชื่อใน lineage ที่ตรงกับ phyla ของกลุ่ม %s" % (o["id"], g["id"]))
        ph = phyla[p_idx]
        hay = [o["scientific_name"], o["name_th"], o["reading_th"], o["name_en"], g["th"], g["en"], ph["name"], ph.get("new_name") or "",
               readings.get(ph["name"], "")]
        for n in names:
            if n != UNKNOWN:
                hay += [n, readings.get(n, "")]
        for t in o["tags"]:
            hay += [tags_by_key[t]["th"], tags_by_key[t]["en"]]
        index.append({
            "id": o["id"], "g": o["group"], "p": p_idx, "sci": o["scientific_name"], "th": o["name_th"],
            "rd": o["reading_th"], "en": o["name_en"], "lv": o["level"], "tags": o["tags"],
            "art": o.get("illustration", ""), "sm": [o["summary_th"], o["summary_en"]],
            "q": " ".join(x for x in hay if x).lower(),
        })
        if synonyms.get(o["id"]):
            index[-1]["sy"] = synonyms[o["id"]]
        if o.get("images"):
            index[-1]["img"] = o["images"][0].get("url_small") or o["images"][0]["url"]
            for im in o["images"]:
                credits.append({"id": o["id"], "sci": o["scientific_name"], "file": im["url"], "author": im["author"], "license": im["license"],
                                "license_url": im.get("license_url", ""), "source_url": im["source_url"], "title": im.get("title", "")})
        detail = {k: v for k, v in o.items() if k not in ("taxon_ids", "id", "group", "scientific_name")}
        detail["id"] = o["id"]
        per_group[o["group"]].append(detail)
    files["index.json"] = index
    files["credits.json"] = credits
    for gid, items in per_group.items():
        used = {x["name"] for o in items for x in o["lineage"]} - {UNKNOWN}
        files["%s.json" % gid] = {
            "group": gid,
            "organisms": items,
            "taxa": {n: {k: taxa[n][k] for k in ("rank", "reading_th", "common_th", "about_th", "about_en")} for n in sorted(used)},
        }
    files["illustrations.json"] = load_json(illustrations_path)
    return files


PRECACHE_SKIP = ("images/", "precache.json", "version.js")


def write_precache(site_dir):
    """รายการไฟล์ที่ service worker เก็บไว้ใช้ออฟไลน์ (ทุกไฟล์ในเว็บ ยกเว้นรูป: รูปเก็บเมื่อเปิดดู) และเวอร์ชัน = แฮชของเนื้อหา
    เวอร์ชันเขียนลง version.js ซึ่ง sw.js นำเข้า (importScripts) เมื่อออกเวอร์ชันใหม่ไฟล์นี้เปลี่ยน เบราว์เซอร์จึงติดตั้ง service worker ใหม่"""
    files = []
    for root, _, names in os.walk(site_dir):
        for n in names:
            rel = os.path.relpath(os.path.join(root, n), site_dir).replace(os.sep, "/")
            if not rel.startswith(PRECACHE_SKIP[0]) and rel not in PRECACHE_SKIP[1:]:
                files.append(rel)
    files.sort()
    h = hashlib.sha1()
    for rel in files:
        h.update(rel.encode("utf-8"))
        with open(os.path.join(site_dir, rel), "rb") as f:
            # CRLF/LF ของ git ไม่ควรทำให้เวอร์ชันต่างกันระหว่างเครื่อง
            h.update(f.read().replace(b"\r\n", b"\n"))
    version = h.hexdigest()[:12]
    with open(os.path.join(site_dir, "version.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write("self.MS2_VERSION = '%s';\n" % version)
    write_min_json(os.path.join(site_dir, "precache.json"), {"version": version, "files": sorted(files + ["version.js"])})
    return version, len(files) + 1


def cmd_build(args):
    """validate ก่อน ถ้ามี error หยุดและไม่เขียนไฟล์ใดๆ แล้วสร้าง site/data/*.json"""
    rep = validate_data(args.data)
    print_report(rep, verbose=False)
    if rep.errors:
        print("หยุด build: ไม่ได้เขียนไฟล์ใดๆ")
        return 1
    try:
        files = build_site_data(args.data, args.illustrations)
    except (BuildError, OSError, ValueError) as e:
        print("หยุด build: %s" % e)
        return 1
    # ลบไฟล์เก่าที่ไม่ได้อยู่ในชุดใหม่ (เช่น กลุ่มที่ถูกลบ) แล้วเขียนใหม่ทั้งหมด
    if os.path.isdir(args.out):
        for old in glob.glob(os.path.join(args.out, "*.json")):
            os.remove(old)
    total = 0
    for name, obj in files.items():
        write_min_json(os.path.join(args.out, name), obj)
        total += os.path.getsize(os.path.join(args.out, name))
    print("build เสร็จ: เขียน %d ไฟล์ใน %s (รวม %.0f KB)" % (len(files), args.out, total / 1024))
    site_dir = os.path.dirname(os.path.abspath(args.out))
    if os.path.basename(os.path.abspath(args.out)) == "data" and os.path.exists(os.path.join(site_dir, "index.html")):
        version, n = write_precache(site_dir)
        print("precache.json: %d ไฟล์ เวอร์ชัน %s" % (n, version))
    return 0


# ---------------------------------------------------------------- images (Wikimedia Commons)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
COMMONS_MIN_INTERVAL = 1.0  # Wikimedia จำกัดอัตราคำขอ (429) จึงช้าและใจเย็น
IMAGES_DIR = os.path.join(ROOT, "site", "images")
MAX_IMAGE_BYTES = 500 * 1024
TARGET_IMAGE_BYTES = 420 * 1024   # เป้าหมายตอนย่อ เผื่อขอบเขต 500 KB
MAX_IMAGE_WIDTH = 1200
MIN_SOURCE_WIDTH = 500
THUMB_WIDTH = 1280                # ขนาดมาตรฐานของ Wikimedia thumbnail
CANDIDATES_PER_QUERY = 50
OK_MIMES = ("image/jpeg", "image/png", "image/webp")
IMAGE_NOTES = "generated/images-notes.json"
IMAGE_OVERRIDES = "images-overrides.json"  # เลือกหรือตัดรูปรายชนิดด้วยมือหลังตรวจ

# ลักษณะรูปที่ให้น้ำหนัก (จุลินทรีย์: รูปจากกล้องจุลทรรศน์ดีกว่ารูปจานเพาะเชื้อ)
MICRO_WORDS = ("microscop", "micrograph", "gram stain", "gram-stain", "stained", "staining", " sem ", " tem ", "scanning electron",
               "transmission electron", "electron micro", "fluoresc", "phase contrast", "phase-contrast", "magnification",
               "cells", "cell ", "bacilli", "cocci", "hyphae", "spores", "trophozoite", "flagell", "cilia")
PLATE_WORDS = ("agar", "petri", "plate", "colony", "colonies", "culture dish", "streak", "growth on", "blood agar", "mackonkey", "macconkey")
BAD_PATTERNS = (r"-g\d{3}", r"\bfig(ure)?s?\.? ?\d", r"\bplos\b", r"\bjournal\b", r"\bpmc\d", r"\.pdf")
BAD_WORDS = ("alignment", "sequence", "protein", "structure", "crystal", "render", "infographic", "anatomy", "manuscript", "diorama",
             "museum", "reconstruction", "exhibit", "statue", "sculpture", "poster", "tree of", "spectr", "analysis", "symptom", "stamp",
             "painting", "engraving", "woodcut", "herbarium", "life cycle", "lifecycle", "crossview", "cross-view", "stereo", "anaglyph", "diagram", "schematic", "scheme", "map", "range", "distribution", "phylogen", "logo", "genome", "gel ", "chromatogram",
             "graph", "chart", "table", "drawing", "illustration", "cladogram", "structure of", "molecule", "skeleton", "label")
GOOD_CATEGORIES = ("featured pictures", "quality images", "valued images", "picture of the day")
# โพรทิสต์ที่เป็นสาหร่ายขนาดใหญ่ ใช้รูปถ่ายธรรมดา (ไม่ต้องใช้กล้องจุลทรรศน์)
MACRO_PROTISTS = {"sargassum-polycystum", "pyropia-yezoensis", "caulerpa-lentillifera", "gracilaria-fisheri", "physarum-polycephalum"}


def normalize_license(short):
    """ชื่อ license จาก Commons -> ชื่อมาตรฐานที่ยอมรับ หรือ None ถ้าไม่ใช่ CC0, CC BY, CC BY-SA, Public domain ที่ชัดเจน
    (CC BY-NC, CC BY-ND, GFDL อย่างเดียว, 'Attribution' ไม่ระบุรุ่น ฯลฯ ไม่รับ)"""
    low = (short or "").strip().lower().replace("–", "-")
    if not low:
        return None
    if re.fullmatch(r"cc[ -]?0( 1\.0)?( universal)?|cc[ -]zero", low):
        return "CC0"
    m = re.fullmatch(r"cc[ -]by[ -]sa[ -](\d\.\d)(?: ([a-z]{2,3}))?", low)
    if m:
        return "CC BY-SA %s%s" % (m.group(1), " " + m.group(2).upper() if m.group(2) else "")
    m = re.fullmatch(r"cc[ -]by[ -](\d\.\d)(?: ([a-z]{2,3}))?", low)
    if m:
        return "CC BY %s%s" % (m.group(1), " " + m.group(2).upper() if m.group(2) else "")
    if low == "public domain" or low.startswith("public domain ") or re.match(r"pd[- ]", low) or low in ("pd", "no known copyright restrictions"):
        return "Public domain"
    return None


ALLOWED_LICENSE_RE = re.compile(r"^(CC0|CC BY \d\.\d( [A-Z]{2,3})?|CC BY-SA \d\.\d( [A-Z]{2,3})?|Public domain)$")


def strip_html(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"), ("&nbsp;", " ")):
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text).strip()


def is_microbe(org):
    """จุลินทรีย์ที่ควรใช้รูปจากกล้องจุลทรรศน์"""
    g = org["group"]
    if g in ("bacteria", "archaea"):
        return True
    if g == "fungi":
        return (org.get("traits") or {}).get("form") in ("yeast", "mold", "chytrid")
    if g == "protists":
        return org["id"] not in MACRO_PROTISTS
    return False


def commons_query(fx, label, params):
    url = COMMONS_API + "?" + urllib.parse.urlencode(dict(params, action="query", format="json", formatversion="2",
                                                          prop="imageinfo", iiprop="url|extmetadata|size|mime",
                                                          iiurlwidth=THUMB_WIDTH,
                                                          iiextmetadatafilter="LicenseShortName|LicenseUrl|Artist|ImageDescription|Categories|ObjectName"))
    data = json.loads(fx.get("commons", label, url))
    return data.get("query", {}).get("pages", [])


def candidate_from_page(page):
    ii = (page.get("imageinfo") or [None])[0]
    if not ii:
        return None
    meta = ii.get("extmetadata") or {}
    val = lambda k: strip_html((meta.get(k) or {}).get("value", ""))  # noqa: E731
    return {
        "title": page.get("title", ""), "thumb": ii.get("thumburl") or "", "original": ii.get("url") or "",
        "page": ii.get("descriptionurl") or "", "width": ii.get("width") or 0, "height": ii.get("height") or 0,
        "mime": ii.get("mime") or "", "license_raw": val("LicenseShortName"), "license_url": val("LicenseUrl"),
        "author": val("Artist"), "desc": val("ImageDescription"), "cats": val("Categories"), "name": val("ObjectName"),
    }


def candidate_ok(c, sci, from_search):
    """ผ่านเมื่อ license เปิดและชัดเจน มีผู้ถ่าย ไฟล์เป็นรูปแรสเตอร์ขนาดพอ และ (ถ้ามาจากการค้นหา) พูดถึงชื่อวิทยาศาสตร์"""
    if not normalize_license(c["license_raw"]):
        return False, "license"
    if c["mime"] not in OK_MIMES or c["width"] < MIN_SOURCE_WIDTH or not c["thumb"]:
        return False, "format"
    if not c["author"]:
        return False, "author"
    if from_search:
        hay = ("%s %s %s" % (c["title"], c["desc"], c["cats"])).lower()
        if sci.lower() not in hay:
            return False, "not-this-species"
    return True, ""


def sci_in_title(c, sci):
    return bool(sci) and sci.lower() in c["title"].lower()


def score_candidate(c, microbe, sci=""):
    text = (" %s %s %s %s " % (c["title"], c["name"], c["desc"], c["cats"])).lower()
    s = 0.0
    micro = sum(1 for w in MICRO_WORDS if w in text)
    plate = sum(1 for w in PLATE_WORDS if w in text)
    bad = sum(1 for w in BAD_WORDS if w in text) + sum(1 for pat in BAD_PATTERNS if re.search(pat, text))
    if microbe:
        s += 6 * min(micro, 3) - 8 * min(plate, 2)
    else:
        s -= 2 * min(plate, 1)
    s -= 8 * min(bad, 2)
    s += 4 * sum(1 for g in GOOD_CATEGORIES if g in text)
    if len(c["title"].split()) > 8:   # ชื่อไฟล์เป็นประโยคยาว มักเป็นรูปประกอบบทความวิจัย
        s -= 6
    if c["mime"] == "image/png":      # กราฟและภาพประกอบมักเป็น PNG รูปถ่ายจริงมักเป็น JPEG
        s -= 3
    if sci_in_title(c, sci):
        s += 3
    s += min(c["width"], 3000) / 1000.0          # ความละเอียดสูงกว่าดีกว่าเล็กน้อย
    return s


def pick_candidates(cands, microbe, limit, sci=""):
    ranked = sorted(cands, key=lambda c: (-score_candidate(c, microbe, sci), c["title"]))
    out, seen = [], set()
    for c in ranked:
        if c["title"] in seen:
            continue
        seen.add(c["title"])
        out.append(c)
        if len(out) >= limit:
            break
    return out


def find_candidates(fx, sci):
    """คืน (ผู้สมัคร, เหตุผลที่ตัดทิ้ง) จากหมวดหมู่ของชนิดนั้นและการค้นหาข้อความ"""
    pages = []
    cat = commons_query(fx, "cat-" + sci, {"generator": "categorymembers", "gcmtitle": "Category:" + sci, "gcmtype": "file",
                                           "gcmlimit": CANDIDATES_PER_QUERY})
    pages += [(p, False) for p in cat]
    srch = commons_query(fx, "search-" + sci, {"generator": "search", "gsrnamespace": 6, "gsrsearch": '"%s"' % sci,
                                               "gsrlimit": CANDIDATES_PER_QUERY})
    pages += [(p, True) for p in srch]
    good, rejected = [], collections.Counter()
    seen = set()
    for page, from_search in pages:
        c = candidate_from_page(page)
        if not c or c["title"] in seen:
            continue
        seen.add(c["title"])
        ok, why = candidate_ok(c, sci, from_search)
        if ok:
            good.append(c)
        else:
            rejected[why] += 1
    return good, rejected, len(seen)


def to_webp(raw, dest):
    """แปลงเป็น WebP ย่อให้กว้างไม่เกิน MAX_IMAGE_WIDTH และไม่เกิน TARGET_IMAGE_BYTES คืน (กว้าง, สูง, ไบต์)"""
    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError("ต้องติดตั้ง Pillow ก่อน: pip install Pillow") from e
    import io
    img = Image.open(io.BytesIO(raw))
    img.load()
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    width = MAX_IMAGE_WIDTH
    while True:
        im = img
        if im.width > width:
            im = im.resize((width, max(1, round(im.height * width / im.width))), Image.LANCZOS)
        for quality in (82, 74, 66, 58, 50, 42):
            buf = io.BytesIO()
            im.save(buf, "WEBP", quality=quality, method=6)
            if buf.tell() <= TARGET_IMAGE_BYTES:
                break
        if buf.tell() <= TARGET_IMAGE_BYTES or width <= 400:
            break
        width = int(width * 0.8)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(buf.getvalue())
    return im.width, im.height, buf.tell()


SMALL_WIDTH = 600


def make_small(src_path, dest_path):
    """ทำรูปขนาดเล็ก (กว้าง 600) จากรูปหลักที่ย่อแล้ว ใช้ในรายการย่อและมือถือเพื่อโหลดเร็ว"""
    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError("ต้องติดตั้ง Pillow ก่อน: pip install Pillow") from e
    img = Image.open(src_path)
    img.load()
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    if img.width > SMALL_WIDTH:
        img = img.resize((SMALL_WIDTH, max(1, round(img.height * SMALL_WIDTH / img.width))), Image.LANCZOS)
    img.save(dest_path, "WEBP", quality=72, method=6)
    return os.path.getsize(dest_path)


def small_name(url):
    return url[:-len(".webp")] + "-600.webp" if url.endswith(".webp") else url + "-600.webp"


def image_record(org_id, n, c, size):
    lic = normalize_license(c["license_raw"])
    return {
        "url": "images/%s/%d.webp" % (org_id, n), "url_small": "images/%s/%d-600.webp" % (org_id, n), "author": c["author"], "license": lic,
        "license_url": c["license_url"], "source_url": c["page"], "title": c["title"], "original_url": c["original"],
        "width": size[0], "height": size[1], "kind": "micrograph" if any(w in (" %s %s " % (c["title"], c["desc"])).lower() for w in MICRO_WORDS[:11]) else "photo",
    }


def save_orgs(path, items):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(items, ensure_ascii=False, indent=2) + "\n")


def cmd_images_variants(args):
    """เพิ่มรูปขนาดเล็ก (-600.webp) ให้รูปที่ยังไม่มี ไม่ใช้เครือข่าย"""
    made = 0
    for path in sorted(glob.glob(os.path.join(args.data, "organisms", "*.json"))):
        items = load_json(path)
        changed = False
        for o in items:
            for img in o.get("images", []):
                src = os.path.normpath(os.path.join(args.images_dir, "..", img["url"]))
                small = small_name(img["url"])
                dest = os.path.normpath(os.path.join(args.images_dir, "..", small))
                if os.path.exists(src) and (img.get("url_small") != small or not os.path.exists(dest)):
                    make_small(src, dest)
                    img["url_small"] = small
                    changed = True
                    made += 1
        if changed:
            save_orgs(path, items)
    print("สร้างรูปขนาดเล็ก %d รูป" % made)
    return 0


def cmd_images(args, fetcher=None):
    if args.check:
        return cmd_images_check(args)
    if args.variants:
        return cmd_images_variants(args)
    fx = fetcher or Fetcher(args.cache, args.refresh, retries=6)
    if fetcher is None:
        fx.intervals["commons"] = COMMONS_MIN_INTERVAL
        fx.intervals["commons-img"] = COMMONS_MIN_INTERVAL
    wanted = set(x.strip() for x in args.only.split(",") if x.strip()) if args.only else None
    notes_path = os.path.join(args.data, IMAGE_NOTES)
    notes = load_json(notes_path) if os.path.exists(notes_path) else {}
    ov_path = os.path.join(args.data, IMAGE_OVERRIDES)
    overrides = load_json(ov_path) if os.path.exists(ov_path) else {}
    done = missing = skipped = 0
    for path in sorted(glob.glob(os.path.join(args.data, "organisms", "*.json"))):
        items = load_json(path)
        changed = False
        for o in items:
            if wanted is not None and o["id"] not in wanted:
                continue
            have = [i for i in o.get("images", []) if os.path.exists(os.path.join(args.images_dir, "..", i["url"]))]
            if have and not args.redo:
                skipped += 1
                continue
            sci = o["scientific_name"]
            try:
                good, rejected, seen = find_candidates(fx, sci)
            except (FetchError, ValueError) as e:
                notes[o["id"]] = "ดึงข้อมูลจาก Commons ไม่สำเร็จ: %s" % e
                print("[%s] ดึงข้อมูลไม่สำเร็จ" % o["id"])
                missing += 1
                continue
            ov = overrides.get(o["id"], {})
            good = [c for c in good if c["title"] not in ov.get("skip", [])]
            picks = pick_candidates(good, is_microbe(o), args.per_species + 3, sci)
            if ov.get("use"):
                forced = [c for c in good if c["title"] == ov["use"]]
                if not forced:  # a file chosen by hand need not be in the species category: look it up by title
                    forced = [c for c in (candidate_from_page(p) for p in commons_query(fx, "title-" + ov["use"], {"titles": ov["use"]})) if c and candidate_ok(c, sci, False)[0]]
                picks = forced + [c for c in picks if c["title"] != ov["use"]]
            saved = []
            for c in picks:
                if len(saved) >= args.per_species:
                    break
                try:
                    raw = fx.get_bytes("commons-img", c["title"], c["thumb"])
                    dest = os.path.join(args.images_dir, o["id"], "%d.webp" % (len(saved) + 1))
                    size = to_webp(raw, dest)
                    make_small(dest, dest[:-len(".webp")] + "-600.webp")
                except (FetchError, OSError, ValueError) as e:
                    print("  ข้าม %s: %s" % (c["title"], e))
                    continue
                saved.append(image_record(o["id"], len(saved) + 1, c, size))
            if saved:
                o["images"] = saved
                notes.pop(o["id"], None)
                changed = True
                done += 1
                print("[%s] %d รูป: %s (%s)" % (o["id"], len(saved), saved[0]["title"], saved[0]["license"]))
            else:
                o["images"] = []
                why = "ไม่พบรูปในหมวดหมู่หรือผลค้นหา (เห็น %d ไฟล์)" % seen if not seen else \
                    "ไม่มีรูปที่ผ่านเกณฑ์ (เห็น %d ไฟล์; ตัดทิ้ง: %s)" % (seen, ", ".join("%s %d" % kv for kv in sorted(rejected.items())) or "ดาวน์โหลดไม่สำเร็จ")
                notes[o["id"]] = why
                changed = True
                missing += 1
                print("[%s] หาไม่ได้: %s" % (o["id"], why))
        if changed:
            save_orgs(path, items)
    os.makedirs(os.path.dirname(notes_path), exist_ok=True)
    with open(notes_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(dict(sorted(notes.items())), ensure_ascii=False, indent=2) + "\n")
    write_images_missing(args.data, args.missing_report)
    print("สรุป: ได้รูป %d ชนิด, หาไม่ได้ %d, ข้าม (มีรูปแล้ว) %d; เรียก API %d ครั้ง ใช้ cache %d ครั้ง" % (done, missing, skipped, fx.stats["api"], fx.stats["cache"]))
    return 0


def write_images_missing(data_dir, out_path):
    notes_path = os.path.join(data_dir, IMAGE_NOTES)
    notes = load_json(notes_path) if os.path.exists(notes_path) else {}
    orgs = load_organisms(data_dir)
    miss = [o for o in orgs if not o.get("images")]
    L = ["# ชนิดที่ยังไม่มีรูปจาก Wikimedia Commons", "",
         "สร้างจาก `python scripts/microsearch.py images` รับเฉพาะ license CC0, CC BY, CC BY-SA, Public domain ที่ระบุชัดเจน",
         "ชนิดในรายการนี้ใช้ภาพวาดเดิมต่อ (ห้ามใช้รูปที่ license ไม่ชัด)", "",
         "ชนิดทั้งหมด %d ชนิด มีรูป %d ชนิด ไม่มีรูป %d ชนิด" % (len(orgs), len(orgs) - len(miss), len(miss)), ""]
    if miss:
        L += ["| ชนิด | กลุ่ม | เหตุผล |", "| --- | --- | --- |"]
        for o in miss:
            L.append("| *%s* (`%s`) | %s | %s |" % (o["scientific_name"], o["id"], o["group"], notes.get(o["id"], "ยังไม่ได้ค้น").replace("|", "/")))
    L.append("")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    return miss


def cmd_images_check(args):
    """ทุกรูปต้องมีเครดิตครบ license เปิด ไฟล์ .webp อยู่จริงและไม่เกิน 500 KB ไม่มีไฟล์เกิน และชนิดที่ไม่มีรูปอยู่ในรายงาน"""
    problems = []
    orgs = load_organisms(args.data)
    base = os.path.abspath(os.path.join(args.images_dir, ".."))
    referenced = set()
    total = 0
    for o in orgs:
        for i, img in enumerate(o.get("images", [])):
            tag = "%s รูปที่ %d" % (o["id"], i + 1)
            total += 1
            for k in ("url", "author", "license", "source_url"):
                if not str(img.get(k, "")).strip():
                    problems.append("%s: ขาด %s" % (tag, k))
            if img.get("license") and not ALLOWED_LICENSE_RE.match(img["license"]):
                problems.append("%s: license %r ไม่อยู่ในที่อนุญาต" % (tag, img["license"]))
            if img.get("source_url") and not str(img["source_url"]).startswith("https://commons.wikimedia.org/"):
                problems.append("%s: source_url ไม่ใช่หน้าไฟล์ของ Commons" % tag)
            small = img.get("url_small")
            if small:
                sp = os.path.normpath(os.path.join(base, small))
                referenced.add(sp)
                if not os.path.exists(sp):
                    problems.append("%s: ไม่พบไฟล์ขนาดเล็ก %s" % (tag, small))
                elif os.path.getsize(sp) > MAX_IMAGE_BYTES:
                    problems.append("%s: ไฟล์ขนาดเล็กใหญ่เกิน" % tag)
            url = img.get("url", "")
            if url:
                path = os.path.normpath(os.path.join(base, url))
                referenced.add(path)
                if not url.endswith(".webp"):
                    problems.append("%s: ไฟล์ต้องเป็น .webp (%s)" % (tag, url))
                if not os.path.exists(path):
                    problems.append("%s: ไม่พบไฟล์ %s" % (tag, url))
                else:
                    size = os.path.getsize(path)
                    if size > MAX_IMAGE_BYTES:
                        problems.append("%s: ไฟล์ใหญ่ %d KB เกิน %d KB" % (tag, size // 1024, MAX_IMAGE_BYTES // 1024))
                    with open(path, "rb") as f:
                        head = f.read(12)
                    if not (head[:4] == b"RIFF" and head[8:12] == b"WEBP"):
                        problems.append("%s: เนื้อไฟล์ไม่ใช่ WebP" % tag)
    if os.path.isdir(args.images_dir):
        for root, _, files in os.walk(args.images_dir):
            for fn in files:
                p = os.path.normpath(os.path.join(root, fn))
                if p not in referenced:
                    problems.append("ไฟล์เกิน ไม่มีชนิดไหนอ้างถึง: %s" % os.path.relpath(p, base).replace(os.sep, "/"))
    miss = [o for o in orgs if not o.get("images")]
    if miss:
        rep = os.path.exists(args.missing_report) and open(args.missing_report, encoding="utf-8").read() or ""
        for o in miss:
            if "`%s`" % o["id"] not in rep:
                problems.append("%s: ไม่มีรูปและไม่อยู่ใน %s (รัน images ใหม่)" % (o["id"], os.path.relpath(args.missing_report, ROOT)))
    for p in problems:
        print("ข้อผิดพลาด: " + p)
    print("ตรวจรูป: %d รูป, ชนิดที่ยังไม่มีรูป %d, ปัญหา %d" % (total, len(miss), len(problems)))
    print("ผ่าน" if not problems else "ไม่ผ่าน")
    return 1 if problems else 0


# ---------------------------------------------------------------- main

def build_parser():
    p = argparse.ArgumentParser(description="Microsearch 2.0 data tools")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("import-seed", help="คัดลอก seed/ ไป data/ (ไม่ทับไฟล์ที่แก้แล้ว)")
    s.add_argument("--force", action="store_true", help="ทับไฟล์ใน data/ โดยไม่ถาม")
    s.add_argument("--seed", default=SEED, help=argparse.SUPPRESS)
    s.add_argument("--data", default=DATA, help=argparse.SUPPRESS)
    s = sub.add_parser("validate", help="ตรวจข้อมูลใน data/")
    s.add_argument("--verbose", action="store_true", help="แสดงรหัสของคำเตือนทั้งหมด")
    s.add_argument("--data", default=DATA, help=argparse.SUPPRESS)
    s = sub.add_parser("fetch", help="ดึง GBIF + NCBI ต่อชนิด (cache ใน cache/)")
    s.add_argument("--refresh", action="store_true", help="ไม่ใช้ cache ยิง API ใหม่")
    s.add_argument("--only", help="ดึงเฉพาะ id เหล่านี้ คั่นด้วยจุลภาค")
    s.add_argument("--data", default=DATA, help=argparse.SUPPRESS)
    s.add_argument("--cache", default=CACHE, help=argparse.SUPPRESS)
    s = sub.add_parser("images", help="หารูปจาก Wikimedia Commons ต่อชนิด (CC0, CC BY, CC BY-SA, Public domain) หรือตรวจด้วย --check")
    s.add_argument("--check", action="store_true", help="ตรวจเครดิต license ขนาด และไฟล์ ไม่ดึงอะไร")
    s.add_argument("--only", help="เฉพาะ id เหล่านี้ คั่นด้วยจุลภาค")
    s.add_argument("--variants", action="store_true", help="สร้างรูปขนาดเล็ก (-600.webp) ให้รูปที่ยังไม่มี")
    s.add_argument("--redo", action="store_true", help="เลือกรูปใหม่แม้ชนิดนั้นมีรูปแล้ว")
    s.add_argument("--refresh", action="store_true", help="ไม่ใช้ cache ยิง API ใหม่")
    s.add_argument("--per-species", type=int, default=1, help="จำนวนรูปต่อชนิด (ค่าเริ่มต้น 1)")
    s.add_argument("--data", default=DATA, help=argparse.SUPPRESS)
    s.add_argument("--cache", default=CACHE, help=argparse.SUPPRESS)
    s.add_argument("--images-dir", default=IMAGES_DIR, help=argparse.SUPPRESS)
    s.add_argument("--missing-report", default=os.path.join(REPORTS, "images-missing.md"), help=argparse.SUPPRESS)
    s = sub.add_parser("coverage", help="นับช่องภาษาอังกฤษที่ยังว่างต่อกลุ่ม เขียน reports/coverage.md")
    s.add_argument("--data", default=DATA, help=argparse.SUPPRESS)
    s.add_argument("--out", default=os.path.join(REPORTS, "coverage.md"), help=argparse.SUPPRESS)
    s = sub.add_parser("build", help="validate แล้วสร้าง site/data/*.json (หยุดถ้ามี error)")
    s.add_argument("--data", default=DATA, help=argparse.SUPPRESS)
    s.add_argument("--out", default=SITE_DATA, help=argparse.SUPPRESS)
    s.add_argument("--illustrations", default=ILLUSTRATIONS, help=argparse.SUPPRESS)
    s = sub.add_parser("taxonomy-diff", help="เทียบ lineage กับที่ดึงมา เขียน reports/taxonomy-diff.md")
    s.add_argument("--data", default=DATA, help=argparse.SUPPRESS)
    s.add_argument("--out", default=os.path.join(REPORTS, "taxonomy-diff.md"), help=argparse.SUPPRESS)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == "import-seed":
        return cmd_import_seed(args)
    if args.cmd == "fetch":
        return cmd_fetch(args)
    if args.cmd == "taxonomy-diff":
        return cmd_taxonomy_diff(args)
    if args.cmd == "build":
        return cmd_build(args)
    if args.cmd == "coverage":
        return cmd_coverage(args)
    if args.cmd == "images":
        return cmd_images(args)
    return cmd_validate(args)


if __name__ == "__main__":
    sys.exit(main())
