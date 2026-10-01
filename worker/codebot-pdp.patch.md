# PDP patch — "Get coding help" button on code-product pages

Apply to: `~/workspace/kestrelattice/build-product-pages.py`
Applies to: whoever next edits this file (code-product coordinator or watcher).
Status: NOT applied yet — this is an exact insertion spec, no conflicts expected
(code coordinator's CODE badge targets build-catalog.py, a different file).

## Goal
On product detail pages for CODE products (zip downloads), show a
"Get coding help" button next to the buy button, linking to /code-bot/.

## How to detect a code product
In `main()`, the pack dict `p` comes from `load_packs()` (pending-listings.jsonl).
Code products are the ones whose `file_path` points at a zip under `formats/code/`
or whose tags include "code". Compute once per product, next to `is_pack`:

```python
fp = str(p.get("file_path", ""))
tags = p.get("tags", []) or []
is_code = fp.endswith(".zip") or "code" in [str(t).lower() for t in tags]
```

and add `is_code=is_code` to the `products.append(dict(...))` call for packs
(the ORIGINALS loop can hardcode `is_code=False`).

## Button HTML
Right after the `buy_html` construction, add:

```python
codebot_html = ""
if pr["is_code"] and is_live:
    codebot_html = (
        f'<p style="margin-top:10px"><a class="btn" '
        f'style="background:transparent;border:1px solid var(--accent);color:var(--accent)" '
        f'href="../../code-bot/?product={pr["gid"]}">Get coding help — ask the bot</a></p>\n'
        f'      <p class="trust">Free with purchase · AI pair-programmer · 20 questions/day</p>')
```

## Template insertion
In the `PAGE` template hero block, change:

```
      {buy_html}
    </div>
```

to:

```
      {buy_html}
      {codebot_html}
    </div>
```

and add `codebot_html=codebot_html` to the `PAGE.format(...)` call.

## Also fix (while here)
The FAQ "How do I receive it?" answer says "The PDF is available for instant
download" — for code products it should say "The ZIP download". Make it
conditional on `is_code`:

```python
receive = ("The ZIP is available for instant download" if pr["is_code"]
           else "The PDF is available for instant download")
```

and use `{receive}` in place of the hardcoded "The PDF is available for instant
download" in the FAQ block.

## Verify
`python3 build-product-pages.py`, then curl a code-product PDP and confirm the
button + link are present; confirm a non-code PDP has no button.
