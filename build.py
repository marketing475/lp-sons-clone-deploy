#!/usr/bin/env python3
"""Build static site from partials + page fragments.

Reads:
- pages.json      — page registry + site metadata
- blog.json       — blog posts (optional, expanded into /blog/{slug}.html pages)
- _partials/head.html   — shared <head> template
- _partials/nav.html    — shared navigation (from <body> through <main> open)
- _partials/footer.html — shared footer + closing scripts
- pages/{fragment}.html — main-content fragment per page

Writes dist/ — deploy-ready static site.
"""
import datetime as _dt
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
PARTIALS = ROOT / "_partials"
PAGES = ROOT / "pages"

SITE_HOST = "https://lpandsonsautocare.com"

# Head content injected for each blog post (BlogPosting schema)
BLOG_POST_HEAD_TEMPLATE = """<script type=\"application/ld+json\">
{
  \"@context\": \"https://schema.org\",
  \"@type\": \"BlogPosting\",
  \"headline\": \"{{TITLE}}\",
  \"datePublished\": \"{{DATE}}\",
  \"author\": {
    \"@type\": \"Person\",
    \"name\": \"{{AUTHOR}}\"
  },
  \"description\": \"{{EXCERPT}}\",
  \"image\": \"{{FEATURED_IMAGE}}\",
  \"mainEntityOfPage\": \"{{SITE_HOST}}/{{SLUG}}/\",
  \"publisher\": {
    \"@type\": \"AutoRepair\",
    \"name\": \"LP & Sons Auto Care\",
    \"telephone\": \"+13866246910\",
    \"address\": {
      \"@type\": \"PostalAddress\",
      \"streetAddress\": \"342 W. New York Ave\",
      \"addressLocality\": \"DeLand\",
      \"addressRegion\": \"FL\",
      \"postalCode\": \"32720\",
      \"addressCountry\": \"US\"
    }
  }
}
</script>"""


def load_json(name):
    p = ROOT / name
    return json.loads(p.read_text()) if p.exists() else None


def render(template, **subs):
    def repl(m):
        return str(subs.get(m.group(1), ""))
    return re.sub(r"\{\{([A-Z_]+)\}\}", repl, template)


def apply_vars(html, variables):
    for k, v in variables.items():
        html = html.replace("{{" + k + "}}", v)
    return html


def assemble(page, head_tpl, nav_html, footer_html, fragment_html, site_defaults=None):
    canonical = page.get("canonical", "")
    default_og_image = page.get(
        "ogImage",
        f"{SITE_HOST}/wp-content/uploads/2020/06/white-stars.png"
    )
    robots = page.get("robots", "")
    robots_tag = f'<meta name="robots" content="{robots}">' if robots else ""
    head = render(
        head_tpl,
        TITLE=page.get("meta_title") or page["title"],
        DESCRIPTION=page["description"],
        PAGE_STYLES=page.get("pageStyles", ""),
        PAGE_ROBOTS=robots_tag,
        CANONICAL=canonical,
        OG_URL=page.get("ogUrl", canonical),
        OG_TITLE=page.get("ogTitle") or page.get("meta_title") or page["title"],
        OG_DESCRIPTION=page.get("ogDescription") or page["description"],
        OG_TYPE=page.get("ogType", "website"),
        OG_IMAGE=default_og_image,
    )
    variables = dict(site_defaults or {})
    variables.update(page.get("vars", {}))
    nav = apply_vars(nav_html, variables)
    frag = apply_vars(fragment_html, variables)
    foot = apply_vars(footer_html, variables)
    return head + nav + "\n" + frag + "\n" + foot


def main():
    cfg = load_json("pages.json")
    if not cfg:
        print("ERROR: pages.json not found")
        return

    blog = load_json("blog.json") or {}
    site = cfg["site"]

    head_tpl = (PARTIALS / "head.html").read_text()
    nav_html = (PARTIALS / "nav.html").read_text()
    footer_html = (PARTIALS / "footer.html").read_text()
    site_defaults = site.get("defaults", {})

    # Reset dist/
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    # Copy static asset directories (WordPress content lives here)
    for static_dir in ("assets", "uploads", "css", "js", "fonts", "images",
                       "wp-content", "wp-includes", "google-fonts"):
        if (ROOT / static_dir).exists():
            shutil.copytree(ROOT / static_dir, DIST / static_dir)

    # Copy CF Pages special files
    for special in ("_redirects", "_headers"):
        if (ROOT / special).exists():
            shutil.copy2(ROOT / special, DIST / special)

    # Copy CF Pages Functions directory (handles URL redirects beyond the
    # ~100-rule _redirects cap on Free tier)
    if (ROOT / "functions").exists():
        shutil.copytree(ROOT / "functions", DIST / "functions")

    # Copy loose root-level static files (nav-fallback.js, favicons, etc.) —
    # anything at the repo root that isn't an HTML page, a build file, or a directory.
    _skip_root_files = {"build.py", "pages.json", "blog.json", ".gitignore", ".DS_Store",
                        "sitemap.xml", "robots.txt", "_redirects", "_headers", "README.md"}
    for item in ROOT.iterdir():
        if not item.is_file():
            continue
        if item.name in _skip_root_files:
            continue
        if item.suffix == ".html":
            continue  # handled by page fragments
        shutil.copy2(item, DIST / item.name)

    written = []

    site_url = site["url"].rstrip("/")

    def canonical_for(slug):
        if slug == "index":
            return f"{site_url}/"
        if slug == "404":
            return f"{site_url}/"
        # All pages (services, locations, blog listing, blog posts) canonicalize
        # at root with trailing slash — matches Google's indexed URLs from the
        # WordPress era, preserving ranking signal through the migration.
        return f"{site_url}/{slug}/"

    # Build content pages
    for page in cfg["pages"]:
        frag_path = PAGES / page["fragment"]
        if not frag_path.exists():
            print(f"  SKIP {page['slug']}: missing fragment {frag_path.name}")
            continue

        page["canonical"] = canonical_for(page["slug"])
        fragment = frag_path.read_text()
        html = assemble(page, head_tpl, nav_html, footer_html, fragment, site_defaults)

        if page["slug"] == "index":
            out = DIST / "index.html"
        elif page["slug"] == "404":
            out = DIST / "404.html"
        else:
            # Folder-style output (dist/slug/index.html) so Cloudflare Pages'
            # default trailing-slash behavior serves it at /slug/ (canonical)
            # and 308-redirects the non-slash variant. Fights against the
            # opposite default that dist/slug.html would trigger.
            out = DIST / page["slug"] / "index.html"

        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html)
        written.append((page["slug"], out.stat().st_size))

    # Build blog posts — output at ROOT with trailing-slash canonical to match
    # Google's indexed URLs from the WordPress era (preserves ranking signal).
    posts = blog.get("posts", [])
    blog_post_frag_path = PAGES / cfg.get("blog", {}).get("postFragment", "blog-post.html")

    if posts:
        # blog_dst kept only for posts.json / rss.xml sidecar files consumed by
        # the /blog/ listing JS. Post HTML files themselves land at DIST root.
        blog_dst = DIST / "blog"
        blog_dst.mkdir(parents=True, exist_ok=True)

        if blog_post_frag_path.exists():
            post_tpl = blog_post_frag_path.read_text()
            for p in posts:
                body = p.get("body", "")
                if not body:
                    print(f"  SKIP blog/{p['slug']}: no body content")
                    continue

                # Human-formatted date
                raw_date = p.get("date", "")
                date_fmt = raw_date
                if raw_date:
                    try:
                        date_fmt = _dt.date.fromisoformat(raw_date).strftime("%B %d, %Y")
                    except Exception:
                        pass
                raw_cat = p.get("category", "")
                cat_display = raw_cat.replace("_", " ").replace("-", " ").title() if raw_cat else ""

                frag = post_tpl
                for k, v in [("TITLE", p["title"]),
                             ("SLUG", p["slug"]),
                             ("DATE", raw_date),
                             ("DATE_FORMATTED", date_fmt),
                             ("AUTHOR", p.get("author", "")),
                             ("BODY", body),
                             ("FEATURED_IMAGE", p.get("featured_image", "")),
                             ("ALT_TEXT", p.get("alt_text", "")),
                             ("CATEGORY", cat_display),
                             ("EXCERPT", p.get("excerpt", ""))]:
                    frag = frag.replace("{{" + k + "}}", v)

                # BlogPosting schema in head
                meta_title = p.get("meta_title") or p["title"]
                description = p.get("description") or p.get("excerpt", "")
                feat = p.get("featured_image", "")
                if feat and not feat.startswith("http"):
                    feat = f"{SITE_HOST}{feat}"
                head_extras = BLOG_POST_HEAD_TEMPLATE
                for k, v in [("TITLE", p["title"].replace('"', '&quot;')),
                             ("META_TITLE", meta_title.replace('"', '&quot;')),
                             ("DESCRIPTION", description.replace('"', '&quot;')),
                             ("SLUG", p["slug"]),
                             ("DATE", raw_date),
                             ("AUTHOR", p.get("author", "")),
                             ("FEATURED_IMAGE", feat),
                             ("SITE_HOST", SITE_HOST),
                             ("EXCERPT", (p.get("excerpt", "") or description).replace('"', '\\"'))]:
                    head_extras = head_extras.replace("{{" + k + "}}", v)

                post_page = {
                    "slug": p["slug"],
                    "title": p["title"],
                    "meta_title": p.get("meta_title", p["title"]),
                    "description": p.get("description") or p.get("excerpt", ""),
                    "canonical": f"{site_url}/{p['slug']}/",
                    "ogUrl": f"{site_url}/{p['slug']}/",
                    "ogType": "article",
                    "ogImage": feat or f"{site_url}/wp-content/uploads/2020/06/white-stars.png",
                    "ogTitle": p.get("meta_title") or p["title"],
                    "ogDescription": p.get("description") or p.get("excerpt", ""),
                    "pageStyles": head_extras,
                }
                html = assemble(post_page, head_tpl, nav_html, footer_html, frag, site_defaults)
                # Folder-style output (dist/slug/index.html) — see note in
                # content-page loop above for the trailing-slash rationale.
                out = DIST / p["slug"] / "index.html"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(html)
                written.append((post_page["slug"], out.stat().st_size))

        # Copy posts.json into dist/blog/ (blog listing JS reads it)
        blog_src_dir = ROOT / "blog"
        if blog_src_dir.exists():
            for item in ("posts.json", "rss.xml"):
                src = blog_src_dir / item
                if src.is_file():
                    shutil.copy2(src, blog_dst / item)
        # Fallback: copy existing posts.json from the source dist if not in root/blog/
        legacy_posts = ROOT / "dist-source-posts.json"
        # Also try preserving the posts.json currently in dist/blog/posts.json if present at repo
        # (Do nothing — build.py resets dist/ first, so we've lost the old one; regenerate.)

    # Regenerate posts.json for /blog/ listing from blog.json (blog page JS reads it)
    if posts:
        listing = {
            "posts": [
                {
                    "title": p["title"],
                    "slug": p["slug"],
                    "excerpt": p.get("excerpt", ""),
                    "date": p.get("date", ""),
                    "category": p.get("category", ""),
                    "featured_image": p.get("featured_image", ""),
                    "author": p.get("author", ""),
                }
                for p in posts
            ]
        }
        (DIST / "blog" / "posts.json").write_text(
            json.dumps(listing, indent=2, ensure_ascii=False)
        )

    # sitemap.xml + robots.txt
    # All pages canonicalize at /slug/ (trailing slash) to match Google's index.
    today = _dt.date.today().isoformat()
    blog_slugs = {p["slug"] for p in posts}
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for slug, _ in written:
        page = next((p for p in cfg["pages"] if p["slug"] == slug), None)
        if page and page.get("noindex"):
            continue
        if slug == "index":
            path = ""
        else:
            path = slug + "/"
        is_blog_post = slug in blog_slugs
        priority = "1.0" if slug == "index" else ("0.6" if is_blog_post else "0.8")
        lines += [
            "  <url>",
            f"    <loc>{site['url']}/{path}</loc>",
            f"    <lastmod>{today}</lastmod>",
            f"    <priority>{priority}</priority>",
            "  </url>",
        ]
    lines.append("</urlset>\n")
    (DIST / "sitemap.xml").write_text("\n".join(lines))
    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {site['url']}/sitemap.xml\n"
    )

    print(f"Wrote {len(written)} pages to {DIST}:")
    for slug, size in written:
        print(f"  {slug:60s} {size:>9,} bytes")
    print("  + sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()
