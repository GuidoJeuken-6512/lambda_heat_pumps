"""Check a built documentation site for broken local images and links.

Zensical warns about dead anchors, but not about an <img> or a link whose
relative path points outside the site — which is how a whole set of
screenshots went missing (see issue #120). This walks the built HTML and
resolves every local `src`/`href` the way a browser would.

Usage:
    python script/check_docs.py docs/site [--build-log build.log]

With --build-log, warnings Zensical printed during the build count as
failures too. Exits non-zero if anything is broken.
"""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

# Attributes that point at something the page needs, per tag.
_CHECKED = {"img": "src", "a": "href", "source": "src", "video": "src"}


class _Refs(HTMLParser):
    """Collect the local references of one page."""

    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = _CHECKED.get(tag)
        if attr is None:
            return
        for name, value in attrs:
            if name == attr and value:
                self.refs.append((tag, value))


def _is_local(ref: str) -> bool:
    parts = urlsplit(ref)
    return not (parts.scheme or parts.netloc or ref.startswith(("#", "/")))


def _target_exists(page: Path, ref: str) -> bool:
    path = unquote(urlsplit(ref).path)
    if not path:
        return True
    target = (page.parent / path).resolve()
    if target.is_file():
        return True
    # A link to a page is a link to its directory's index.html.
    return (target / "index.html").is_file()


def check_site(site: Path) -> list[str]:
    """Every broken local reference in the built site, as readable lines."""
    site = site.resolve()
    problems: list[str] = []
    for page in sorted(site.rglob("*.html")):
        parser = _Refs()
        parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        for tag, ref in parser.refs:
            if not _is_local(ref):
                continue
            if not _target_exists(page, ref):
                problems.append(f"{page.relative_to(site)}: <{tag}> {ref}")
            elif not str((page.parent / unquote(urlsplit(ref).path)).resolve()).startswith(
                str(site)
            ):
                problems.append(f"{page.relative_to(site)}: <{tag}> {ref} (outside the site)")
    return problems


def check_build_log(log: Path) -> list[str]:
    """The warnings Zensical printed while building."""
    text = re.sub(r"\x1b\[[0-9;]*m", "", log.read_text(encoding="utf-8", errors="replace"))
    problems: list[str] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(("Warning", "Error")):
            # The next line names the file and position: "╭─[ path:line:col ]".
            where = lines[index + 1].strip(" ╭─[]") if index + 1 < len(lines) else ""
            problems.append(f"{where}: {line}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("site", type=Path, help="the built site, e.g. docs/site")
    parser.add_argument("--build-log", type=Path, help="Zensical's build output")
    args = parser.parse_args()

    if not args.site.is_dir():
        print(f"No built site at {args.site}", file=sys.stderr)
        return 2

    problems = check_site(args.site)
    if args.build_log:
        problems += check_build_log(args.build_log)

    for problem in problems:
        print(problem)
    print(f"{len(problems)} problem(s) found")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
