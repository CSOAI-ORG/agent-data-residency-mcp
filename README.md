# Agent Data Residency MCP


> ## Buy Starter — £29/mo
> **Signed attestations + unlimited audits + email support.**
> 👉 **[Subscribe at meok.ai](https://buy.stripe.com/6oU00l5Sc28aaAt0Q88k83Z)** — instant HMAC signing key + Stripe-managed billing.
>
> Free tier remains MIT-licensed and zero-config. Upgrade only when you need signed compliance artefacts for audit.

[![PyPI](https://img.shields.io/pypi/v/agent-data-residency-mcp)](https://pypi.org/project/agent-data-residency-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-A2A-purple)](https://meok.ai)

**The only MCP server that answers "where does this data live?" at agent runtime.**

When agent A (EU) talks to agent B (US), where does data flow? Is GDPR Chapter V satisfied? Does the transfer need an adequacy decision, SCCs, or BCRs? This MCP gives programmatic answers.

## Why this exists

Enterprises rolling out multi-agent systems hit a runtime question nobody answers cleanly: **when agent A in Frankfurt invokes a tool on agent B in Virginia, what just happened legally?**

Most MCPs ignore the transfer. Compliance teams audit it months later. This MCP makes the answer a single tool call.

## Install

```bash
pip install agent-data-residency-mcp
```

## Tools

| Tool | Purpose |
|------|---------|
| `check_residency_policy` | Source→target verdict (permitted / restricted / prohibited) with legal basis |
| `get_transfer_basis` | List GDPR Chapter V mechanisms: adequacy, SCCs, BCRs, derogations, UK IDTA |
| `list_adequacy_decisions` | All 16 current EU adequacy decisions with scope + warnings |
| `check_eu_ai_act_data_governance` | Article 10 duties + cross-refs to GDPR Chapter V |
| `log_transfer` | Pro+ — immutable audit log entry (pairs with agent-audit-logger-mcp) |

## Example

```python
result = check_residency_policy(
    source_region="DE",
    target_region="US",
    data_classification="personal"
)
```

Returns:
```json
{
  "verdict": "permitted-with-conditions",
  "rationale": "Adequacy decision for united-states (2023-07-10). Scope: EU-US Data Privacy Framework certified organisations only",
  "legal_basis": "GDPR Article 45 — adequacy decision",
  "warning": "Subject to ongoing CJEU scrutiny. Schrems III risk."
}
```

## Pairs with

- `agent-audit-logger-mcp` — immutable A2A audit trail
- `agent-policy-enforcement-mcp` — define per-region transfer policies
- `eu-ai-act-compliance-mcp` — Article 10 data-governance check

## Pricing

- **Free**: 10 calls/day. All check tools.
- **Pro** £79/mo: unlimited + `log_transfer` audit trail. [Subscribe](https://buy.stripe.com/14A4gB3K4eUWgYR56o8k836)
- **Enterprise** £1,499/mo: white-label + on-premise. hello@meok.ai

## License

MIT © MEOK AI Labs

<!-- meok-faq-schema-v1 -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Is this MCP server free to use?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. The free tier gives you 10 calls per day with no API key required. Pro tier is £79/mo for unlimited calls plus cryptographically signed attestations your auditor can verify independently."
      }
    },
    {
      "@type": "Question",
      "name": "How does the signed attestation work?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Every Pro tier audit produces a HMAC-SHA256 signed certificate with a unique ID and a public verify URL. Your auditor pastes the cert into https://meok-attestation-api.vercel.app/verify and gets an independent valid/invalid response. No contact with MEOK required."
      }
    },
    {
      "@type": "Question",
      "name": "Which MCP clients does this work with?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "All standard MCP clients: Claude Desktop, Claude Code, Cursor, VS Code with MCP extension, Windsurf, Cline, and any custom MCP-compatible agent. Install via npx meok-setup or pip install for the underlying Python package."
      }
    },
    {
      "@type": "Question",
      "name": "Can I install all MEOK governance MCPs at once?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. Run npx meok-setup --pack governance to install all 10 governance MCPs and write the configs for Claude Desktop, Cursor, or Windsurf in one command."
      }
    },
    {
      "@type": "Question",
      "name": "Is the regulation text authoritative?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. MEOK syncs daily from the EUR-Lex Cellar SPARQL endpoint, the canonical EU regulation publication system. The text is verbatim with no LLM summarization. Every quote is auditor-defensible and includes the exact article number plus relevance score."
      }
    }
  ]
}
</script>


## Sister MCPs

Part of the MEOK **A2a** pack — designed to work together as a fleet. Install the whole pack with `npx meok-setup --pack a2a`, or pick the ones you need:

- **Prompt Injection Firewall** → `uvx agent-prompt-injection-firewall-mcp` · [PyPI](https://pypi.org/project/agent-prompt-injection-firewall-mcp/) · [GitHub](https://github.com/CSOAI-ORG/agent-prompt-injection-firewall-mcp)
- **Certified Handoff** → `uvx agent-handoff-certified-mcp` · [PyPI](https://pypi.org/project/agent-handoff-certified-mcp/) · [GitHub](https://github.com/CSOAI-ORG/agent-handoff-certified-mcp)
- **Policy Enforcement** → `uvx agent-policy-enforcement-mcp` · [PyPI](https://pypi.org/project/agent-policy-enforcement-mcp/) · [GitHub](https://github.com/CSOAI-ORG/agent-policy-enforcement-mcp)
- **Audit Logger** → `uvx agent-audit-logger-mcp` · [PyPI](https://pypi.org/project/agent-audit-logger-mcp/) · [GitHub](https://github.com/CSOAI-ORG/agent-audit-logger-mcp)
- **Rate Limiter** → `uvx agent-rate-limiter-mcp` · [PyPI](https://pypi.org/project/agent-rate-limiter-mcp/) · [GitHub](https://github.com/CSOAI-ORG/agent-rate-limiter-mcp)

Full catalogue + Anthropic Registry verify links: [meok.ai/anthropic-registry](https://meok.ai/anthropic-registry)

<!-- mcp-name: io.github.CSOAI-ORG/agent-data-residency-mcp -->
