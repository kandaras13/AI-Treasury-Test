# Security, Privacy, and Responsible-AI Notes

## Threat model highlights

**Sensitive document exposure**
- Prototype: no persistence; local OCR; no third-party API.
- Production: encryption, least privilege, retention policy, access logging, approved storage boundary.

**Malicious uploads**
- Prototype: restricted image extensions and image-size guardrails.
- Production: MIME validation, malware scanning, decompression-bomb protection, per-user quotas.

**Model/OCR error**
- Never convert uncertain extraction directly into regulatory approval.
- `REVIEW` exists specifically to preserve human judgment.
- Maintain test sets across beverage type, image quality, camera angle, glare, and typography.

**Prompt injection**
- This prototype does not execute instructions from labels and does not use an LLM, so text printed on an uploaded label cannot instruct the application to change behavior.
- If an LLM/vision-language model is introduced, label text must be treated as untrusted data, not instructions.

**Auditability**
- Production should record model/version, deterministic rule version, input hash, extracted fields, decision, reviewer overrides, and timestamps.

## Responsible AI

The safest automation target is routine comparison, not final adjudication. Agents remain responsible for nuanced interpretation. The tool should be evaluated for:
- false approvals,
- false rejections,
- OCR performance across image quality,
- latency,
- reviewer override rates,
- drift after model upgrades.

A rollout should begin in shadow mode, comparing tool outputs to existing agent decisions before affecting workflow.
