"""Explicit per-product PDP slug overrides (Gumroad id -> unique slug).

Two distinct products whose titles differ only by punctuation slugify to the
same PDP slug (e.g. 'API Key Lifecycle Checklist' vs 'API-Key Lifecycle
Checklist'), so the second product's Details link landed on the first
product's page. Both build-catalog.py (card hrefs) and build-product-pages.py
(page dirs) consult this map so card hrefs and page dirs agree.
Convention: the newer product keeps the base slug; the older one gets '-2'.
"""
SLUG_OVERRIDES = {
    # 'API-Key Lifecycle Checklist' (2026-09-30) vs 'API Key Lifecycle
    # Checklist' (2026-10-01, keeps base)
    "nawurj": "api-key-lifecycle-checklist-2",
    # 'Audit-Logging Tool Vendor Scorecard' (2026-09-30) vs 'Audit Logging
    # Tool Vendor Scorecard' (2026-10-01, keeps base)
    "qvntl": "audit-logging-tool-vendor-scorecard-2",
    # 'Blast-Radius Mapping Worksheet' (2026-09-30) vs 'Blast Radius
    # Mapping Worksheet' (2026-10-01, keeps base)
    "berqf": "blast-radius-mapping-worksheet-2",
}
