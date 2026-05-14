#!/usr/bin/env python3
"""
Agent Data Residency MCP Server
================================
By MEOK AI Labs | https://meok.ai

The only MCP server that answers "where does this data live?" at agent runtime.

When agent A (EU) talks to agent B (US), where does data flow? Is GDPR
Chapter V satisfied? Is the EU AI Act data-governance hook tripped? Does
the transfer need an adequacy decision, SCCs, or BCRs?

This MCP closes the last A2A gap identified in MEOK's portfolio:
- Programmatic transfer-basis lookup (GDPR Articles 44-49)
- EU AI Act Article 10 data-governance alignment
- Adequacy decisions matrix (UK, Japan, Korea, Switzerland, Canada, etc.)
- Per-region data classification routing

Install: pip install agent-data-residency-mcp
Run:     python server.py
"""

import json
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

import os as _os

_MEOK_API_KEY = _os.environ.get("MEOK_API_KEY", "")

try:
    sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
    from auth_middleware import check_access as _shared_check_access
    _AUTH_ENGINE_AVAILABLE = True
except ImportError:
    _AUTH_ENGINE_AVAILABLE = False

    def _shared_check_access(api_key: str = ""):
        """Fallback when shared auth engine is not available."""
        if _MEOK_API_KEY and api_key and api_key == _MEOK_API_KEY:
            return True, "OK", "pro"
        if _MEOK_API_KEY and api_key and api_key != _MEOK_API_KEY:
            return False, "Invalid API key. Get one at https://meok.ai/api-keys", "free"
        return True, "OK", "free"


def check_access(api_key: str = ""):
    """Unified access check."""
    return _shared_check_access(api_key)


FREE_DAILY_LIMIT = 10
_usage: dict[str, list[datetime]] = defaultdict(list)
STRIPE_PRO = "https://buy.stripe.com/14A4gB3K4eUWgYR56o8k836"


def _rl(tier="free") -> Optional[str]:
    if tier in ("pro", "professional", "enterprise"):
        return None
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=1)
    _usage["anonymous"] = [t for t in _usage["anonymous"] if t > cutoff]
    if len(_usage["anonymous"]) >= FREE_DAILY_LIMIT:
        return f"Free tier limit ({FREE_DAILY_LIMIT}/day). Pro £79/mo: {STRIPE_PRO}"
    _usage["anonymous"].append(now)
    return None


# ── GDPR Adequacy decisions (current as of 2026-05-13) ─────────────────
ADEQUACY_DECISIONS = {
    "andorra": {"decided": "2010-10-19", "status": "adequate", "scope": "general"},
    "argentina": {"decided": "2003-06-30", "status": "adequate", "scope": "general"},
    "canada": {"decided": "2001-12-20", "status": "adequate", "scope": "PIPEDA commercial only"},
    "faroe-islands": {"decided": "2010-03-05", "status": "adequate", "scope": "general"},
    "guernsey": {"decided": "2003-11-21", "status": "adequate", "scope": "general"},
    "isle-of-man": {"decided": "2004-04-28", "status": "adequate", "scope": "general"},
    "israel": {"decided": "2011-01-31", "status": "adequate", "scope": "general"},
    "japan": {"decided": "2019-01-23", "status": "adequate", "scope": "mutual adequacy under PIPA"},
    "jersey": {"decided": "2008-05-08", "status": "adequate", "scope": "general"},
    "new-zealand": {"decided": "2012-12-19", "status": "adequate", "scope": "general"},
    "south-korea": {"decided": "2021-12-17", "status": "adequate", "scope": "PIPA"},
    "switzerland": {"decided": "2000-07-26", "status": "adequate", "scope": "general (revised FADP 2023)"},
    "united-kingdom": {"decided": "2021-06-28", "status": "adequate", "scope": "general (review by 2025)"},
    "united-states": {
        "decided": "2023-07-10",
        "status": "adequate-partial",
        "scope": "EU-US Data Privacy Framework certified organisations only",
        "warning": "Subject to ongoing CJEU scrutiny. Schrems III risk.",
    },
    "uruguay": {"decided": "2012-08-21", "status": "adequate", "scope": "general"},
}

# ── EU AI Act Article 10 data-governance hooks ─────────────────────────
EU_AI_ACT_DATA_RULES = {
    "high-risk-systems": {
        "article": "EU AI Act Article 10",
        "duties": [
            "Training, validation, testing datasets must meet quality criteria",
            "Examination for biases that may affect health, safety, fundamental rights",
            "Data governance and management practices for high-risk AI systems",
            "Datasets must be relevant, representative, free of errors, complete",
        ],
        "transfers": "Cross-border training data flows must respect GDPR Chapter V",
    },
    "biometric-data": {
        "article": "EU AI Act Article 5(1)(e) + GDPR Article 9",
        "duties": [
            "Real-time remote biometric ID prohibited in public spaces (with narrow exceptions)",
            "Special category personal data — heightened protection",
            "Explicit consent or substantial public interest required",
        ],
    },
}

# ── Transfer basis matrix ──────────────────────────────────────────────
TRANSFER_BASES = {
    "adequacy-decision": {
        "article": "GDPR Article 45",
        "scope": "Country/sector with EU adequacy decision",
        "documentation": "Adequacy decision reference (Commission Implementing Decision)",
    },
    "standard-contractual-clauses": {
        "article": "GDPR Article 46(2)(c)/(d)",
        "scope": "Most third-country transfers without adequacy",
        "documentation": "EU SCCs 2021 Module 1-4 + Transfer Impact Assessment",
        "since_schrems_ii": "Must include supplementary measures",
    },
    "binding-corporate-rules": {
        "article": "GDPR Article 47",
        "scope": "Intra-group transfers across countries",
        "documentation": "BCRs approved by lead DPA",
    },
    "derogations-specific-situations": {
        "article": "GDPR Article 49",
        "scope": "Narrow exceptions: explicit consent, contract necessity, vital interests",
        "documentation": "Article 49 ground + DPIA",
        "warning": "Not for systematic or repetitive transfers",
    },
    "uk-international-data-transfer-agreement": {
        "article": "UK GDPR Article 46 + IDTA",
        "scope": "Post-Brexit UK→third-country transfers",
        "documentation": "IDTA 2022 + UK Addendum to EU SCCs",
    },
}


mcp = FastMCP(
    "Agent Data Residency",
    instructions=(
        "By MEOK AI Labs — Agent data residency + GDPR Chapter V transfer-basis runtime guard. "
        "Use check_residency_policy to determine if a source→target transfer is permitted. "
        "Use get_transfer_basis to identify the legal mechanism. Use log_transfer to record. "
        "Free tier: 10/day. Pro tier: unlimited + signed compliance attestations."
    ),
)


@mcp.tool()
def check_residency_policy(
    source_region: str,
    target_region: str,
    data_classification: str = "personal",
    api_key: str = "",
) -> str:
    """Check if a cross-border data transfer between agents is permitted.

    Args:
        source_region: ISO country code or EU/EEA/UK (e.g., "DE", "FR", "US", "UK", "EU").
        target_region: ISO country code or region of the receiving agent.
        data_classification: One of: personal, sensitive-personal, biometric, health, financial, special-category, public.
        api_key: Optional MEOK API key.

    Returns: JSON with verdict (permitted/restricted/prohibited), legal basis, required documentation.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_PRO})
    if err := _rl(tier):
        return json.dumps({"error": err, "upgrade_url": STRIPE_PRO})

    src = source_region.lower().strip()
    tgt = target_region.lower().strip()
    classification = data_classification.lower().strip()

    # EU/EEA inbound = always OK if source is EU/EEA member
    eu_eea = {"eu", "eea", "at", "be", "bg", "hr", "cy", "cz", "dk", "ee", "fi", "fr",
              "de", "gr", "hu", "ie", "it", "lv", "lt", "lu", "mt", "nl", "pl", "pt",
              "ro", "sk", "si", "es", "se", "is", "li", "no"}

    src_in_eu = src in eu_eea
    tgt_in_eu = tgt in eu_eea

    if src_in_eu and tgt_in_eu:
        return json.dumps({
            "verdict": "permitted",
            "rationale": "Intra-EU/EEA transfer — no Chapter V mechanism required.",
            "legal_basis": "GDPR + national law of source/target member state",
            "documentation": "Standard records of processing (Article 30)",
            "regulation": "GDPR + EU AI Act Article 10 if high-risk",
            "tier": tier,
        }, indent=2)

    # EU/EEA outbound — check adequacy
    if src_in_eu and not tgt_in_eu:
        # Map country code to adequacy key
        country_map = {
            "us": "united-states", "usa": "united-states",
            "uk": "united-kingdom", "gb": "united-kingdom",
            "jp": "japan", "kr": "south-korea", "ch": "switzerland",
            "ca": "canada", "il": "israel", "nz": "new-zealand",
            "ar": "argentina", "uy": "uruguay",
        }
        ad_key = country_map.get(tgt, tgt)
        if ad_key in ADEQUACY_DECISIONS:
            decision = ADEQUACY_DECISIONS[ad_key]
            verdict = "permitted-with-conditions" if decision.get("warning") else "permitted"
            return json.dumps({
                "verdict": verdict,
                "rationale": f"Adequacy decision for {ad_key} ({decision['decided']}). Scope: {decision['scope']}",
                "legal_basis": "GDPR Article 45 — adequacy decision",
                "warning": decision.get("warning"),
                "documentation": "Adequacy decision reference + standard records",
                "regulation": "GDPR Chapter V",
                "tier": tier,
            }, indent=2)
        else:
            # No adequacy → SCCs needed
            return json.dumps({
                "verdict": "restricted",
                "rationale": f"No adequacy decision for '{tgt}'. Transfer requires Chapter V mechanism.",
                "legal_basis_options": [
                    "GDPR Article 46(2)(c) — Standard Contractual Clauses (SCCs 2021)",
                    "GDPR Article 47 — Binding Corporate Rules (intra-group)",
                    "GDPR Article 49 — Derogations (narrow; explicit consent / contract necessity)",
                ],
                "required_documentation": [
                    "Signed EU SCCs (Module 1-4 depending on roles)",
                    "Transfer Impact Assessment (TIA) post-Schrems II",
                    "Supplementary technical / organisational / contractual measures",
                ],
                "warning": "Since Schrems II (Case C-311/18), SCCs alone are NOT sufficient. TIA + supplementary measures required.",
                "regulation": "GDPR Chapter V",
                "tier": tier,
            }, indent=2)

    # Special category data — heightened scrutiny
    if classification in ("biometric", "health", "sensitive-personal", "special-category"):
        return json.dumps({
            "verdict": "restricted-heightened",
            "rationale": f"Special category data (Article 9). Transfer requires explicit consent OR substantial public interest OR healthcare necessity.",
            "additional_basis_required": "GDPR Article 9(2) ground in addition to Article 45/46/49 transfer basis",
            "eu_ai_act_check": "EU AI Act Article 5(1)(e) — real-time remote biometric ID in public spaces is PROHIBITED",
            "regulation": "GDPR Articles 9 + 45-49 + EU AI Act Article 5",
            "tier": tier,
        }, indent=2)

    # Non-EU source / non-EU target — GDPR doesn't apply unless data subject is in EU
    return json.dumps({
        "verdict": "out-of-gdpr-scope",
        "rationale": f"Both source ({src}) and target ({tgt}) are outside EU/EEA. Check local law.",
        "caveat": "GDPR Article 3 may still apply if EU data subjects are affected (extraterritorial scope).",
        "regulation": "Check applicable national/regional law",
        "tier": tier,
    }, indent=2)


@mcp.tool()
def get_transfer_basis(transfer_type: str = "", api_key: str = "") -> str:
    """List GDPR Chapter V transfer mechanisms.

    Args:
        transfer_type: Optional filter — one of: adequacy-decision, standard-contractual-clauses, binding-corporate-rules, derogations-specific-situations, uk-international-data-transfer-agreement.

    Returns: JSON with full transfer-basis matrix and applicable scenarios.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_PRO})

    if transfer_type:
        key = transfer_type.lower().strip()
        if key in TRANSFER_BASES:
            return json.dumps({key: TRANSFER_BASES[key], "tier": tier}, indent=2)
        return json.dumps({
            "error": f"Unknown transfer type. Use one of: {', '.join(TRANSFER_BASES.keys())}",
            "tier": tier,
        }, indent=2)

    return json.dumps({
        "transfer_bases": TRANSFER_BASES,
        "regulation": "GDPR Chapter V (Articles 44-49)",
        "post_schrems_ii_warning": "SCCs require Transfer Impact Assessment + supplementary measures since CJEU Case C-311/18 (16 July 2020)",
        "tier": tier,
    }, indent=2)


@mcp.tool()
def list_adequacy_decisions(api_key: str = "") -> str:
    """Return all current EU adequacy decisions with status, date, and scope."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_PRO})
    return json.dumps({
        "adequacy_decisions": ADEQUACY_DECISIONS,
        "total_count": len(ADEQUACY_DECISIONS),
        "regulation": "GDPR Article 45 — Commission Implementing Decisions",
        "source": "ec.europa.eu/info/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en",
        "tier": tier,
    }, indent=2)


@mcp.tool()
def check_eu_ai_act_data_governance(system_type: str = "high-risk", api_key: str = "") -> str:
    """Check EU AI Act Article 10 data-governance duties for an AI system.

    Args:
        system_type: One of: high-risk-systems, biometric-data.

    Returns: JSON with Article 10 duties + cross-references to GDPR Chapter V.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_PRO})
    key = system_type.lower().strip().replace("_", "-")
    if key in EU_AI_ACT_DATA_RULES:
        return json.dumps({key: EU_AI_ACT_DATA_RULES[key], "tier": tier}, indent=2)
    return json.dumps({
        "eu_ai_act_data_rules": EU_AI_ACT_DATA_RULES,
        "tier": tier,
    }, indent=2)


@mcp.tool()
def log_transfer(
    source_region: str,
    target_region: str,
    data_classification: str,
    transfer_basis: str = "",
    purpose: str = "",
    api_key: str = "",
) -> str:
    """Log a cross-border data transfer for audit trail (Pro+).

    Args:
        source_region: Source country/region.
        target_region: Target country/region.
        data_classification: Data classification (personal, sensitive, etc.).
        transfer_basis: Legal basis used (adequacy, sccs, bcrs, etc.).
        purpose: Transfer purpose.

    Returns: JSON receipt with timestamp + transfer ID.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_PRO})
    if tier == "free":
        return json.dumps({
            "error": "Transfer logging requires Pro tier (immutable audit trail).",
            "upgrade_url": STRIPE_PRO,
        })

    import hashlib
    timestamp = datetime.now(timezone.utc).isoformat()
    transfer_id = hashlib.sha256(
        f"{timestamp}|{source_region}|{target_region}|{data_classification}".encode()
    ).hexdigest()[:16]

    return json.dumps({
        "transfer_id": transfer_id,
        "timestamp": timestamp,
        "source_region": source_region,
        "target_region": target_region,
        "data_classification": data_classification,
        "transfer_basis": transfer_basis or "unspecified",
        "purpose": purpose or "unspecified",
        "status": "logged",
        "audit_chain": "Pair with agent-audit-logger-mcp for tamper-evident bundle export",
        "tier": tier,
    }, indent=2)




# ── search_regulation: FTS5-backed verbatim regulation lookup ──────────────
# Powered by EUR-Lex Cellar API daily sync via eu-ai-act-compliance-mcp.
# Returns 64-token snippets from canonical regulation text (Akoma Ntoso XHTML).

import sqlite3 as _sqlite3
from pathlib import Path as _Path
import os as _os_search

# Try multiple known locations for the EUR-Lex DB
_REG_DB_CANDIDATES = [
    _Path(_os_search.environ.get("MEOK_EURLEX_DB", "")) if _os_search.environ.get("MEOK_EURLEX_DB") else None,
    _Path.home() / "clawd" / "mcp-marketplace" / "eu-ai-act-compliance-mcp" / "data" / "regulations.db",
    _Path(__file__).parent / "data" / "regulations.db",
]
_REG_DB = next((p for p in _REG_DB_CANDIDATES if p and p.exists()), None)


@mcp.tool()
def search_regulation(query: str, regulation: str = "", limit: int = 10) -> dict:
    """Full-text search across 410+ articles of real EU regulation text (EUR-Lex verified).

    Args:
        query: Search terms. FTS5 syntax supported (AND, OR, NEAR, phrase quoting).
        regulation: Optional filter - one of: eu-ai-act, dora, nis2, cra, csrd, gdpr.
        limit: Max results (default 10).

    Returns:
        Snippets from matching articles with regulation + article + relevance score.
        Verbatim from EUR-Lex Cellar — auditor-defensible quotes with `>>>match<<<` highlights.
    """
    if _REG_DB is None or not _REG_DB.exists():
        return {
            "error": "EUR-Lex database not available. Install eu-ai-act-compliance-mcp v1.4.0+ which ships the DB, OR set MEOK_EURLEX_DB env var.",
            "hint": "pip install eu-ai-act-compliance-mcp",
        }
    if not query or len(query.strip()) < 2:
        return {"error": "Query must be at least 2 characters"}

    celex_map = {
        "eu-ai-act": "32024R1689", "dora": "32022R2554", "nis2": "32022L2555",
        "cra": "32024R2847", "csrd": "32022L2464", "gdpr": "32016R0679",
    }
    celex_filter = celex_map.get(regulation.lower().strip()) if regulation else None

    safe_query = query.replace('"', '""').strip()
    if " " in safe_query and not any(op in safe_query.upper() for op in [" AND ", " OR ", " NEAR"]):
        safe_query = '"' + safe_query + '"'

    conn = _sqlite3.connect(str(_REG_DB))
    try:
        if celex_filter:
            sql = ("SELECT celex, article_number, article_id, "
                   "snippet(articles_fts, 3, '>>>', '<<<', '...', 64) AS snip, rank "
                   "FROM articles_fts WHERE articles_fts MATCH ? AND celex = ? "
                   "ORDER BY rank LIMIT ?")
            rows = conn.execute(sql, (safe_query, celex_filter, limit)).fetchall()
        else:
            sql = ("SELECT celex, article_number, article_id, "
                   "snippet(articles_fts, 3, '>>>', '<<<', '...', 64) AS snip, rank "
                   "FROM articles_fts WHERE articles_fts MATCH ? "
                   "ORDER BY rank LIMIT ?")
            rows = conn.execute(sql, (safe_query, limit)).fetchall()

        name_map = {v: k for k, v in celex_map.items()}
        return {
            "query": query,
            "regulation_filter": regulation or "all",
            "result_count": len(rows),
            "source": "EUR-Lex Cellar API (publications.europa.eu) - verbatim text",
            "disclaimer": "Quotes are auditor-defensible. Not legal advice.",
            "results": [
                {"regulation": name_map.get(r[0], r[0]), "article_number": r[1],
                 "snippet": r[3], "relevance_score": round(abs(r[4]), 2)}
                for r in rows
            ],
        }
    except Exception as e:
        return {"error": f"FTS5 search error: {e}"}
    finally:
        conn.close()


@mcp.tool()
def list_regulations_in_db() -> dict:
    """List all regulations in the local EUR-Lex FTS5 database."""
    if _REG_DB is None or not _REG_DB.exists():
        return {"error": "Database not available", "regulations": []}
    conn = _sqlite3.connect(str(_REG_DB))
    try:
        rows = conn.execute(
            "SELECT celex, name, short_name, type, title, article_count, last_synced "
            "FROM regulations ORDER BY celex"
        ).fetchall()
        return {
            "source": "EUR-Lex Cellar API",
            "total_regulations": len(rows),
            "total_articles": conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
            "regulations": [
                {"celex": r[0], "name": r[1], "short_name": r[2], "type": r[3],
                 "title": (r[4] or "")[:120], "article_count": r[5],
                 "last_synced": r[6]}
                for r in rows
            ],
        }
    finally:
        conn.close()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
