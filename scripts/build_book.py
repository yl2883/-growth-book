#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert the Word manuscript into js/book-data.js for the static ebook site."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
DOCX = Path(
    "/Users/a57321/Library/Containers/com.tencent.xinWeChat/Data/Documents/"
    "xwechat_files/wxid_oomc1gzm72rv22_1341/msg/file/2026-02/"
    "借你十年成长文字的光2026.01(正).docx"
)
OUT = ROOT / "js" / "book-data.js"


def soft(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("，", ",").replace("。", ".").replace("：", ":")
    s = s.replace("（", "(").replace("）", ")")
    s = s.replace("—", "-").replace("–", "-").replace("－", "-")
    s = re.sub(r"-{2,}", "-", s)
    s = s.replace("·", "").replace("•", "").replace(" ", "").replace("\u3000", "")
    s = s.replace("、", "").replace(",", "").replace(".", "")
    return s


def strip_num(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^\d+\s*[\.、．]\s*", "", s)
    s = re.sub(r"^[一二三四五六七八九十]+[、．.]\s*", "", s)
    return s.strip()


def is_date(s: str) -> bool:
    return bool(re.match(r"^(19|20)\d{2}年", s))


def slugify(text: str, used: set[str]) -> str:
    base = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text).strip("-") or "sec"
    out = base
    n = 2
    while out in used:
        out = f"{base}-{n}"
        n += 1
    used.add(out)
    return out


TITLE_ALIASES = {
    soft("花开的声音"): [soft("倾听花开的声音"), soft("花开的声音")],
    soft("我迷恋家乡的树"): [soft("我迷恋家乡的榕树"), soft("4.我迷恋家乡的榕树")],
    soft("爱在故乡的土壤里"): [soft("爱在家乡的土壤里")],
    soft("在文字与成长中寻找光"): [soft("在成长的文字中寻找光"), soft("2.在成长的文字中寻找光")],
    soft("治愈你的是那个你未曾涉足的广阔世界"): [
        soft("治愈你的是那个未曾涉足的广阔世界"),
        soft("1.治愈你的是那个未曾涉足的广阔世界"),
    ],
    soft("（后记）文字之舟：载我们渡过教育的河流"): [
        soft("文字之舟：载我们渡过教育的河流"),
        soft("（后记）文字之舟：载我们渡过教育的河流"),
    ],
    soft("忽略的,往往是最重要的"): [soft("忽略的，往往是最重要的")],
    soft("二、友谊万岁"): [soft("二、 友谊万岁"), soft("二、友谊万岁")],
    soft("一个时光倒流的梦"): [soft("1. 一个时光倒流的梦"), soft("1.一个时光倒流的梦")],
    soft("一、把阳光带回家"): [soft("吾爱吾家"), soft("把阳光带回家")],
    soft("第一次观光之舞"): [soft("光之舞"), soft("6.光之舞")],
    soft("思考多么重要"): [soft("思考,多么重要"), soft("5.思考,多么重要")],
}


def split_dash_title(title: str) -> tuple[str, str | None]:
    """Split '主标题——副标题' forms that appear on one TOC line."""
    for sep in ("——", "—", "--", "–"):
        if sep in title:
            left, right = title.split(sep, 1)
            left, right = left.strip(), (sep + right).strip()
            if left:
                return left, right
    return title, None


def title_keys(title: str) -> list[str]:
    keys = []
    main, _sub = split_dash_title(title)
    candidates = [
        title,
        main,
        strip_num(title),
        strip_num(main),
        re.sub(r"\s+", " ", title),
        re.sub(r"\s+", "", title),
        re.sub(r"\s+", "", main),
        # collapse multiple dashes for Part 1 titles
        re.sub(r"[-—–]+", "-", title),
        re.sub(r"[-—–]+", "-", main),
    ]
    for candidate in candidates:
        k = soft(candidate)
        # also soft after dash collapse
        k2 = soft(re.sub(r"[-—–]+", "-", candidate))
        for item in (k, k2):
            if item and item not in keys:
                keys.append(item)
    for alias in TITLE_ALIASES.get(soft(title), []):
        if alias not in keys:
            keys.append(alias)
    for alias in TITLE_ALIASES.get(soft(strip_num(title)), []):
        if alias not in keys:
            keys.append(alias)
    for alias in TITLE_ALIASES.get(soft(strip_num(main)), []):
        if alias not in keys:
            keys.append(alias)
    return keys


def paras_match(body: str, title: str) -> bool:
    body_s = soft(body)
    body_plain = soft(strip_num(body))
    for key in title_keys(title):
        if body_s == key or body_plain == key:
            return True
        # 【拾遗】... trailing note
        if key.startswith(soft("【拾遗】")) and body_s.startswith(soft("【拾遗】")):
            return True
        if key == soft("【拾遗】") and body_s.startswith(soft("【拾遗】")):
            return True
        if key == soft("【妈妈有话说】") and body_s.startswith(soft("【妈妈有话说】")):
            return True
        # body title may be longer with note
        if body_plain.startswith(key) and len(key) >= 4:
            return True
        if key.startswith(body_plain) and len(body_plain) >= 4 and len(body_plain) >= len(key) * 0.7:
            return True
    # special: section without numbering
    if re.match(r"^[一二三四五六七八九十]+[、．.]", title):
        if soft(body) == soft(strip_num(title)):
            return True
    return False


def classify_toc(t: str) -> str:
    if re.match(r"^第[一二三四]辑", t):
        return "part"
    if t.startswith("（后记）") or t.startswith("(后记)"):
        return "epilogue"
    if t in ("【妈妈有话说】", "【拾遗】"):
        return "group"
    if re.match(r"^[一二三四五六七八九十]+[、．.]", t):
        return "section"
    if t.startswith("——") or t.startswith("—"):
        return "subtitle"
    return "article"


def main() -> None:
    doc = Document(str(DOCX))
    paras = [p.text.replace("\u00a0", " ").strip() for p in doc.paragraphs]

    toc_i = next(i for i, t in enumerate(paras) if t == "目录")
    ji = [i for i, t in enumerate(paras) if re.match(r"^第[一二三四]辑", t)]
    body_start = ji[4]
    preface_start = next(i for i, t in enumerate(paras) if t.startswith("自序"))

    # ---- TOC nodes ----
    toc_lines = [t for t in paras[toc_i + 1 : body_start] if t]
    nodes = []
    used_ids: set[str] = set()
    current_part = None
    current_section = None
    current_group = None
    i = 0
    while i < len(toc_lines):
        t = toc_lines[i]
        kind = classify_toc(t)
        if kind == "subtitle":
            if nodes and nodes[-1]["kind"] == "article":
                nodes[-1]["subtitle"] = t
            i += 1
            continue
        if kind == "part":
            current_part = re.sub(r"\s+", " ", t)
            current_section = None
            current_group = None
            title = current_part
        elif kind == "section":
            current_section = t
            current_group = None
            title = t
        elif kind == "group":
            current_group = t
            title = t
        elif kind == "epilogue":
            current_part = "后记"
            current_section = None
            current_group = None
            title = t
        else:
            title = t

        # TOC sometimes keeps "标题——副标题" on one line
        inline_sub = None
        if kind == "article":
            main, inline_sub = split_dash_title(title)
            title = main

        node = {
            "id": slugify(strip_num(title) if kind == "article" else title, used_ids),
            "title": title,
            "display": strip_num(title) if kind == "article" and re.match(r"^\d+", title) else title,
            "kind": kind,
            "part": current_part,
            "section": current_section,
            "group": current_group if kind == "article" else (t if kind == "group" else None),
        }
        if inline_sub:
            node["subtitle"] = inline_sub
        if kind == "article" and i + 1 < len(toc_lines) and classify_toc(toc_lines[i + 1]) == "subtitle":
            node["subtitle"] = toc_lines[i + 1]
            i += 1
        nodes.append(node)
        i += 1

    # ---- Linear match body ----
    # Expected matchable nodes in order (all except we still match parts/sections/groups)
    expect = list(nodes)
    starts: list[int | None] = [None] * len(expect)
    ei = 0
    for bi, text in enumerate(paras):
        if bi < body_start or not text:
            continue
        if ei >= len(expect):
            break
        # Try current expected; also allow skipping a failed optional? No - try current only,
        # but if current fails for long, try look-ahead of 1-2 for stuck groups/aliases
        matched = False
        for look in range(0, 6):
            if ei + look >= len(expect):
                break
            candidate = expect[ei + look]
            if paras_match(text, candidate["title"]) or (
                candidate.get("subtitle") and paras_match(text, candidate["title"] + candidate["subtitle"])
            ):
                starts[ei + look] = bi
                ei = ei + look + 1
                matched = True
                break
        if not matched:
            continue

    unmatched = [expect[i]["title"] for i in range(len(expect)) if starts[i] is None]
    print(f"nodes={len(expect)} unmatched={len(unmatched)}")
    for t in unmatched[:30]:
        print("  unmatched:", t)

    # Fill content ranges
    def next_start(idx: int) -> int:
        for j in range(idx + 1, len(starts)):
            if starts[j] is not None:
                return starts[j]  # type: ignore
        return len(paras)

    def to_blocks(start: int, end: int, node: dict) -> list[tuple[str, str]]:
        blocks: list[tuple[str, str]] = []
        first = True
        for k in range(start, end):
            t = paras[k]
            if not t:
                continue
            if first:
                first = False
                if paras_match(t, node["title"]) or t.startswith("【拾遗】") or t.startswith("【妈妈有话说】"):
                    if t.startswith("【拾遗】") and len(t) > 4:
                        rest = re.sub(r"^【拾遗】", "", t).strip()
                        if rest:
                            blocks.append(("note", rest))
                    continue
                if node["kind"] == "section" and soft(t) == soft(strip_num(node["title"])):
                    continue
            if node.get("subtitle") and (t == node["subtitle"] or t.startswith("——")):
                blocks.append(("subtitle", t))
            elif is_date(t):
                blocks.append(("date", t))
            elif re.match(r"^【.+】$", t):
                blocks.append(("label", t))
            elif re.match(r"^（[一二三四五六七八九十\d]+）", t) or re.match(
                r"^\([一二三四五六七八九十\d]+\)", t
            ):
                blocks.append(("subhead", t))
            elif (
                re.match(r"^[一二三四五六七八九十]+[、．.]", t)
                and len(t) < 60
                and node["kind"] in ("article", "epilogue", "group")
            ):
                blocks.append(("subhead", t))
            else:
                blocks.append(("p", t))
        return blocks

    def blocks_to_html(blocks: list[tuple[str, str]], title: str, subtitle: str | None = None) -> str:
        parts = [f'<h1 class="chapter-title">{html.escape(title)}</h1>']
        if subtitle:
            parts.append(f'<p class="subtitle">{html.escape(subtitle)}</p>')
        for kind, t in blocks:
            esc = html.escape(t).replace("\n", "<br>")
            if kind == "p":
                parts.append(f"<p>{esc}</p>")
            elif kind == "date":
                parts.append(f'<p class="date">{esc}</p>')
            elif kind == "subtitle":
                parts.append(f'<p class="subtitle">{esc}</p>')
            elif kind == "label":
                parts.append(f'<p class="label">{esc}</p>')
            elif kind == "subhead":
                parts.append(f'<h3 class="subhead">{esc}</h3>')
            elif kind == "note":
                parts.append(f'<p class="note">{esc}</p>')
            else:
                parts.append(f"<p>{esc}</p>")
        return "\n".join(parts)

    # Preface
    pref_blocks: list[tuple[str, str]] = []
    for t in paras[preface_start + 1 : toc_i]:
        if not t:
            continue
        pref_blocks.append(("date", t) if is_date(t) else ("p", t))

    pages = [
        {
            "id": "preface",
            "title": "自序——传递明朗与欢乐",
            "part": "卷首",
            "section": "",
            "group": "",
            "kind": "preface",
            "html": blocks_to_html(pref_blocks, "自序——传递明朗与欢乐"),
        }
    ]

    # Build pages for articles + epilogue; parts/sections/groups are TOC only
    # Also create pages for section/group only if they have unique intro content? Skip.
    page_id_by_node: dict[int, str] = {}
    for idx, node in enumerate(nodes):
        if node["kind"] not in ("article", "epilogue"):
            continue
        start = starts[idx]
        if start is None:
            # still create empty stub? skip empty
            print("skip missing article:", node["title"])
            continue
        end = next_start(idx)
        blocks = to_blocks(start, end, node)
        # Avoid including following structural titles mistakenly - already bounded by next_start
        page = {
            "id": node["id"],
            "title": node["display"],
            "part": node.get("part") or "",
            "section": node.get("section") or "",
            "group": node.get("group") or "",
            "kind": node["kind"],
            "html": blocks_to_html(blocks, node["display"], node.get("subtitle")),
        }
        pages.append(page)
        page_id_by_node[idx] = node["id"]

    # TOC for UI
    toc = [{"id": "preface", "title": "自序——传递明朗与欢乐", "level": 1, "kind": "preface", "pageId": "preface"}]
    for idx, node in enumerate(nodes):
        if node["kind"] == "part":
            level, kind = 1, "part"
        elif node["kind"] == "section":
            level, kind = 2, "section"
        elif node["kind"] == "group":
            level, kind = 3, "group"
        elif node["kind"] == "epilogue":
            level, kind = 1, "epilogue"
        else:
            level, kind = 3, "article"

        page_id = page_id_by_node.get(idx)
        if page_id is None:
            # point to next available page
            for j in range(idx + 1, len(nodes)):
                if j in page_id_by_node:
                    page_id = page_id_by_node[j]
                    break
            if page_id is None and pages:
                page_id = pages[-1]["id"]

        toc.append(
            {
                "id": node["id"],
                "title": node["display"] if node["kind"] == "article" else node["title"],
                "level": level,
                "kind": kind,
                "pageId": page_id,
            }
        )

    book = {
        "title": "借你十年成长文字的光",
        "titleLine1": "借你十年成长",
        "titleLine2": "文字的光",
        "author": "天风 著",
        "quote": "愿你历经岁月，依旧向阳生长。",
        "quoteLines": ["愿你历经岁月，", "依旧向阳生长。"],
        "cover": "images/cover.jpg",
        "pages": pages,
        "toc": toc,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("window.BOOK_DATA = " + json.dumps(book, ensure_ascii=False) + ";\n", encoding="utf-8")

    nonempty = sum(1 for p in pages if len(re.sub(r"<[^>]+>", "", p["html"])) > 40)
    print(f"pages={len(pages)} nonempty={nonempty} toc={len(toc)}")
    print("wrote", OUT, OUT.stat().st_size)
    print("first pages:", [p["title"] for p in pages[:10]])
    print("last pages:", [p["title"] for p in pages[-6:]])


if __name__ == "__main__":
    main()
