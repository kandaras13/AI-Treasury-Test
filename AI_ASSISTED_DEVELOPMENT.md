# AI-Assisted Development Notes

This submission was developed with AI assistance as an engineering productivity tool.

## How AI was used

AI was used to help:
- decompose stakeholder notes into functional and non-functional requirements,
- identify edge cases,
- scaffold the application structure,
- draft unit tests and documentation,
- review the implementation for security, UX, and maintainability concerns.

## Human verification approach

AI-generated suggestions were treated as drafts rather than authority. Regulatory facts were checked against current TTB guidance. The architecture was intentionally changed away from a cloud vision API because stakeholder notes describe outbound network restrictions.

## Example prompt strategy

A useful implementation prompt was structured around:
1. **Role/context** — act as a senior engineer building a federal proof-of-concept.
2. **Ground truth** — provide stakeholder notes and explicit TTB requirements.
3. **Constraints** — no external API dependency, target ~5 seconds, batch uploads, simple UI, human-in-the-loop.
4. **Output contract** — working source tree, tests, README, security notes.
5. **Quality checks** — do not invent requirements; flag uncertain compliance cases for human review.

This format keeps the model focused on testable requirements and makes assumptions explicit.
