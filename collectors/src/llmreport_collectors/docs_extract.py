"""Docs-HTML extraction rules — versioned code, never LLM output (design.md 1.2.3).

Each registered docs source carries an ``extraction_rule_id`` in
registry/sources.json; the rule's behaviour lives here under that id. Output
is the canonical docs-html snapshot ``{page_url, extracted[], extraction_rule_id}``.

Extraction is deliberately resilient (structure hashes + section diffing, not
brittle selectors alone):

- the content root is located through a priority-ordered fallback chain
  (rule-specific marker -> <article> -> <main> -> <body>);
- boilerplate subtrees (script/style/nav/header/footer/aside/svg) are dropped;
- sections are keyed by stable heading slugs (or date markers where the page
  renders no headings) and carry an NFC-normalized visible-text hash, so
  markup/styling-only churn never surfaces (materiality ignore: cosmetic);
- if a page yields no sections at all, extraction degrades to ONE whole-page
  text-hash item (``page[text-hash]``) so change detection never goes blind.

Model-list rules (``mistral-models-index-v1``, ``xai-changelog-v1``) emit
``models[<id>]`` items; the docs differ maps their added/removed deltas to
model.released / model.deprecated per DOCS_MODEL_EVENTS (the materiality
table's ``by-extraction-rule`` hook). Section items are never auto-classified:
their deltas land in the exceptions queue as diff.unclassified.
"""

from __future__ import annotations

import hashlib
import html as html_mod
import re
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser

MISTRAL_MODELS_RULE_ID = "mistral-models-index-v1"
XAI_MODELS_RULE_ID = "xai-changelog-v1"
OPENAI_CHANGELOG_RULE_ID = "openai-changelog-v1"
ANTHROPIC_RELEASE_NOTES_RULE_ID = "anthropic-release-notes-v1"
GOOGLE_CHANGELOG_RULE_ID = "google-gemini-changelog-v1"
AZURE_WHATS_NEW_RULE_ID = "azure-whats-new-v1"

#: Subtrees that are never content. NOTE: <template> is deliberately NOT
#: skipped — platform.claude.com serves its docs content inside declarative
#: shadow-DOM templates, which ARE the rendered content.
_SKIP_TAGS = frozenset(
    {"script", "style", "noscript", "svg", "nav", "header",
     "footer", "aside", "form", "iframe"}
)
_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
     "meta", "param", "source", "track", "wbr"}
)
_HEADING_RE = re.compile(r"^h([1-6])$")

#: Month-year grouping line, e.g. "July, 2026" (openai changelog).
_MONTH_LINE_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|October|"
    r"November|December),?\s+(20\d\d)$"
)
#: Entry date line, e.g. "Jul 6" (openai changelog).
_ENTRY_LINE_RE = re.compile(
    r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})$"
)
#: xAI model ids as they appear in the models-page section text.
_XAI_MODEL_ID_RE = re.compile(r"\bgrok-[a-z0-9.][a-z0-9.\-]*\b")
#: Mistral docs-mirror models index: `import <ident> from './<slug>';`
_TS_IMPORT_RE = re.compile(r"^import\s+\w+\s+from\s+'\./([a-z0-9\-]+)';?\s*$")


@dataclass(frozen=True)
class DocsRule:
    """One versioned extraction rule."""

    rule_id: str
    strategy: str  # headings | date-lines | models | ts-imports
    #: content-root fallback chain: ("class-prefix", x) | ("tag", x)
    roots: tuple[tuple[str, str], ...] = (("tag", "article"), ("tag", "main"))
    heading_levels: frozenset[int] = frozenset({2, 3})
    hierarchical: bool = False  # key sub-headings under their parent heading
    model_id_re: re.Pattern | None = None


RULES: dict[str, DocsRule] = {
    OPENAI_CHANGELOG_RULE_ID: DocsRule(
        rule_id=OPENAI_CHANGELOG_RULE_ID,
        strategy="date-lines",
        # The changelog is an Astro island; its class prefix is stable while
        # the style-hash suffix is not — match the prefix, fall back to main.
        roots=(("class-prefix", "_ChangelogPage"), ("tag", "main")),
    ),
    ANTHROPIC_RELEASE_NOTES_RULE_ID: DocsRule(
        rule_id=ANTHROPIC_RELEASE_NOTES_RULE_ID,
        strategy="headings",
        roots=(("tag", "article"), ("tag", "main")),
        heading_levels=frozenset({2, 3}),
    ),
    GOOGLE_CHANGELOG_RULE_ID: DocsRule(
        rule_id=GOOGLE_CHANGELOG_RULE_ID,
        strategy="headings",
        roots=(("tag", "article"), ("tag", "main")),
        heading_levels=frozenset({2}),
    ),
    AZURE_WHATS_NEW_RULE_ID: DocsRule(
        rule_id=AZURE_WHATS_NEW_RULE_ID,
        strategy="headings",
        roots=(("tag", "main"), ("tag", "article")),
        heading_levels=frozenset({2, 3}),
        hierarchical=True,
    ),
    XAI_MODELS_RULE_ID: DocsRule(
        rule_id=XAI_MODELS_RULE_ID,
        strategy="models",
        roots=(("tag", "main"), ("tag", "article")),
        heading_levels=frozenset({3}),
        model_id_re=_XAI_MODEL_ID_RE,
    ),
    MISTRAL_MODELS_RULE_ID: DocsRule(
        rule_id=MISTRAL_MODELS_RULE_ID,
        strategy="ts-imports",
    ),
}

#: Rule-declared event types for models[] deltas (materiality by-extraction-rule).
#: Anything not declared here falls through to diff.unclassified.
DOCS_MODEL_EVENTS: dict[str, dict[str, str]] = {
    MISTRAL_MODELS_RULE_ID: {"added": "model.released", "removed": "model.deprecated"},
    XAI_MODELS_RULE_ID: {"added": "model.released", "removed": "model.deprecated"},
}


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def text_hash(text: str) -> str:
    """16-hex hash over the NFC-normalized, whitespace-collapsed text."""
    collapsed = re.sub(r"\s+", " ", _nfc(text)).strip()
    return hashlib.sha256(collapsed.encode("utf-8")).hexdigest()[:16]


def slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", _nfc(text).lower()).strip("-")
    return slug[:max_len].strip("-") or "untitled"


@dataclass
class _Block:
    kind: str  # heading | text
    level: int | None
    text: str


class _ContentExtractor(HTMLParser):
    """Streams the visible text of the content region(s) as heading/text blocks.

    EVERY element matching the root spec is captured (a page may hold several
    <article> regions and the content one is not necessarily first). Region
    and skip-subtree extents are tracked by TAG-NAME nesting counters (not raw
    tag depth), so the extractor stays correct on real-world HTML with
    unclosed <p>/<li>/... elements.
    """

    def __init__(self, root: tuple[str, str]) -> None:
        super().__init__(convert_charrefs=True)
        self._root_kind, self._root_value = root
        self._capturing = False
        self._root_tag: str | None = None
        self._root_nesting = 0
        self._skip_tag: str | None = None
        self._skip_nesting = 0
        self._heading_level: int | None = None
        self._heading_buf: list[str] = []
        self._text_buf: list[str] = []
        self.blocks: list[_Block] = []
        self.found_root = False

    # -- root matching -----------------------------------------------------
    def _matches_root(self, tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        if self._root_kind == "tag":
            return tag == self._root_value
        if self._root_kind == "class-prefix":
            for name, value in attrs:
                if name == "class" and value:
                    for cls in value.split():
                        if cls.startswith(self._root_value):
                            return True
        return False

    # -- flush helpers -------------------------------------------------------
    def _flush_text(self) -> None:
        text = "\n".join(t for t in self._text_buf if t)
        self._text_buf = []
        if text.strip():
            self.blocks.append(_Block("text", None, text))

    def finish(self) -> None:
        """Flush any open buffers (EOF inside the root)."""
        self._flush_text()

    # -- parser hooks ----------------------------------------------------------
    def handle_starttag(self, tag, attrs):  # noqa: ANN001
        if tag in _VOID_TAGS:
            return
        if not self._capturing:
            if self._matches_root(tag, attrs):
                self.found_root = True
                self._capturing = True
                self._root_tag = tag
                self._root_nesting = 0
            return
        if self._skip_tag is not None:
            if tag == self._skip_tag:
                self._skip_nesting += 1
            return
        if tag == self._root_tag:
            self._root_nesting += 1
        if tag in _SKIP_TAGS:
            self._skip_tag = tag
            self._skip_nesting = 0
            return
        m = _HEADING_RE.match(tag)
        if m and self._heading_level is None:
            self._flush_text()
            self._heading_level = int(m.group(1))
            self._heading_buf = []

    def handle_endtag(self, tag):  # noqa: ANN001
        if tag in _VOID_TAGS or not self._capturing:
            return
        if self._skip_tag is not None:
            if tag == self._skip_tag:
                if self._skip_nesting > 0:
                    self._skip_nesting -= 1
                else:
                    self._skip_tag = None
            return
        if self._heading_level is not None and _HEADING_RE.match(tag):
            heading = "".join(self._heading_buf)
            # icon fonts render as private-use codepoints inside headings
            heading = "".join(
                c for c in heading if unicodedata.category(c) not in ("Co", "Cc", "Cf")
            )
            heading = re.sub(r"\s+", " ", heading).strip()
            if heading:
                self.blocks.append(_Block("heading", self._heading_level, heading))
            self._heading_level = None
            self._heading_buf = []
            return
        if tag == self._root_tag:
            if self._root_nesting > 0:
                self._root_nesting -= 1
            else:
                # leaving this content region: flush; a later element matching
                # the root spec opens the next region
                self._heading_level = None
                self._skip_tag = None
                self._flush_text()
                self._capturing = False

    def handle_data(self, data):  # noqa: ANN001
        if not self._capturing or self._skip_tag is not None:
            return
        if self._heading_level is not None:
            self._heading_buf.append(data)
            return
        chunk = data.strip()
        if chunk:
            self._text_buf.append(chunk)


def _extract_blocks(html: str, rule: DocsRule) -> list[_Block]:
    """Blocks of the first root in the rule's fallback chain that matches."""
    for root in (*rule.roots, ("tag", "body")):
        parser = _ContentExtractor(root)
        try:
            parser.feed(html)
            parser.close()
            parser.finish()  # EOF inside the root: flush open buffers
        except Exception:  # noqa: BLE001 — malformed HTML: try the next root
            continue
        if parser.found_root and parser.blocks:
            return parser.blocks
    return []


def _dedup_key(key: str, used: dict[str, int]) -> str:
    n = used.get(key, 0) + 1
    used[key] = n
    return key if n == 1 else f"{key}-{n}"


def _sections_from_headings(
    blocks: list[_Block], rule: DocsRule
) -> list[tuple[str, str, str]]:
    """[(key, heading, section_text)] keyed by (hierarchical) heading slugs."""
    levels = rule.heading_levels
    top = min(levels) if levels else 2
    sections: list[tuple[str, str, list[str]]] = []
    used: dict[str, int] = {}
    parent_slug: str | None = None
    open_section = False
    for block in blocks:
        if block.kind == "heading":
            if block.level in levels:
                slug = slugify(block.text)
                if rule.hierarchical:
                    if block.level == top:
                        parent_slug = slug
                        key = slug
                    else:
                        key = f"{parent_slug}/{slug}" if parent_slug else slug
                else:
                    key = slug
                sections.append((_dedup_key(key, used), block.text, []))
                open_section = True
            elif block.level is not None and block.level < top:
                # a more-major heading closes the current section: its
                # content must not be attributed to the section above it
                open_section = False
                parent_slug = None
        elif block.kind == "text" and open_section and sections:
            sections[-1][2].append(block.text)
    return [(k, h, "\n".join(t)) for k, h, t in sections]


def _sections_from_date_lines(blocks: list[_Block]) -> list[tuple[str, str, str]]:
    """Sections for heading-less changelogs rendered as date-marker lines."""
    lines: list[str] = []
    for block in blocks:
        lines.extend(l.strip() for l in block.text.splitlines())
    sections: list[tuple[str, str, list[str]]] = []
    used: dict[str, int] = {}
    month_slug: str | None = None
    month_text = ""
    for line in lines:
        if not line:
            continue
        if _MONTH_LINE_RE.match(line):
            month_slug = slugify(line)
            month_text = line
            continue
        if _ENTRY_LINE_RE.match(line):
            key = f"{month_slug}/{slugify(line)}" if month_slug else slugify(line)
            heading = f"{month_text} {line}".strip()
            sections.append((_dedup_key(key, used), heading, []))
            continue
        if sections:
            sections[-1][2].append(line)
    return [(k, h, "\n".join(t)) for k, h, t in sections]


def _items_from_sections(sections: list[tuple[str, str, str]]) -> list[dict]:
    return [
        {
            "field_path": f"sections[{key}]",
            "value": {"heading": heading, "content_hash": text_hash(text)},
        }
        for key, heading, text in sections
    ]


def _items_models(sections: list[tuple[str, str, str]], rule: DocsRule) -> list[dict]:
    items: list[dict] = []
    seen_models: set[str] = set()
    for key, heading, text in sections:
        match = rule.model_id_re.search(text) if rule.model_id_re else None
        if match and match.group(0) not in seen_models:
            model_id = match.group(0)
            seen_models.add(model_id)
            items.append(
                {
                    "field_path": f"models[{model_id}]",
                    "value": {
                        "name": heading,
                        "model_id": model_id,
                        "content_hash": text_hash(text),
                    },
                }
            )
        else:
            items.append(
                {
                    "field_path": f"sections[{key}]",
                    "value": {"heading": heading, "content_hash": text_hash(text)},
                }
            )
    return items


def _items_ts_imports(text: str) -> list[dict]:
    items = []
    seen: set[str] = set()
    for line in text.splitlines():
        m = _TS_IMPORT_RE.match(line.strip())
        if m and m.group(1) not in seen:
            slug = m.group(1)
            seen.add(slug)
            items.append(
                {"field_path": f"models[{slug}]", "value": {"model_id": slug}}
            )
    return items


def _visible_text(html: str) -> str:
    parser = _ContentExtractor(("tag", "body"))
    try:
        parser.feed(html)
        parser.close()
        parser.finish()
    except Exception:  # noqa: BLE001
        return html_mod.unescape(re.sub(r"<[^>]+>", " ", html))
    if parser.blocks:
        return "\n".join(b.text for b in parser.blocks)
    return html_mod.unescape(re.sub(r"<[^>]+>", " ", html))


def extract_docs(rule_id: str, payload: str, page_url: str) -> tuple[dict, dict]:
    """Apply the versioned extraction rule -> (docs-html snapshot, sidecar)."""
    rule = RULES[rule_id]
    if rule.strategy == "ts-imports":
        items = _items_ts_imports(payload)
        if not items:  # degraded parse: whole-file hash keeps diffing alive
            items = [
                {
                    "field_path": "page[text-hash]",
                    "value": {"content_hash": text_hash(payload)},
                }
            ]
    else:
        blocks = _extract_blocks(payload, rule)
        if rule.strategy == "date-lines":
            sections = _sections_from_date_lines(blocks)
            items = _items_from_sections(sections)
        elif rule.strategy == "models":
            sections = _sections_from_headings(blocks, rule)
            items = _items_models(sections, rule)
        else:  # headings
            sections = _sections_from_headings(blocks, rule)
            items = _items_from_sections(sections)
        if not items:
            items = [
                {
                    "field_path": "page[text-hash]",
                    "value": {"content_hash": text_hash(_visible_text(payload))},
                }
            ]
    items.sort(key=lambda i: i["field_path"])
    snapshot = {
        "page_url": page_url,
        "extracted": items,
        "extraction_rule_id": rule_id,
    }
    sidecar_models = {
        item["value"]["model_id"]: {
            "modalities": [],
            "name": item["value"].get("name"),
        }
        for item in items
        if item["field_path"].startswith("models[")
    }
    sidecar = {"rule_id": rule_id, "models": sidecar_models}
    return snapshot, sidecar


def model_ids_from_snapshot(snapshot: dict | None) -> list[str]:
    """models[<id>] ids of a docs-html snapshot (parity-check helper)."""
    if not snapshot:
        return []
    out = []
    for item in snapshot.get("extracted", []):
        path = item.get("field_path", "")
        if path.startswith("models[") and path.endswith("]"):
            out.append(path[len("models[") : -1])
    return out
