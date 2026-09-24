# Architecture and Engineering Notes

## Request flow

1. **Streamlit UI** receives application values and one or more label images.
2. **Image preprocessing** applies EXIF orientation correction, resize guardrails, grayscale conversion, local contrast enhancement, and light denoising.
3. **Local Tesseract OCR** extracts text, confidence, and token boxes.
4. **Verification engine** applies field-specific rules:
   - Brand/class/producer/country: normalized fuzzy matching.
   - ABV: numeric extraction and exact numeric comparison.
   - Proof: optional consistency check against 2× ABV.
   - Net contents: unit normalization.
   - Health warning: prescribed wording + capitalization/header check.
5. **Decision layer** produces PASS, REVIEW, or FAIL.
6. **UI** displays field-level explanations, timing, OCR text, and batch CSV export.

## Cloud-native path

This prototype is deliberately small, but the components map cleanly to a cloud-native implementation:

- UI/API -> Azure App Service or Azure Container Apps
- OCR/verification -> containerized stateless service
- Batch work -> Service Bus queue + worker pool
- Metadata/audit -> Azure SQL/Cosmos DB depending retention needs
- Images -> short-lived encrypted Blob Storage only if policy requires retention
- Identity -> Microsoft Entra ID / managed identity
- Secrets -> Azure Key Vault
- Observability -> Application Insights / Log Analytics
- CI/CD -> GitHub Actions or Azure DevOps with SAST/dependency scanning

## Scaling batch imports

For 200-300 images, a production version should enqueue each label and process in parallel with bounded concurrency. The user would see progressive results and retry failed jobs without reprocessing successful items.

## Performance strategy

The prototype uses a single OCR pass after lightweight preprocessing to preserve the stakeholder's speed requirement. Expensive multi-pass enhancement should be reserved for low-confidence images rather than applied to every label.

## Security-by-design

- No external ML API dependency.
- No prototype file persistence.
- No credentials required.
- Upload type restrictions.
- Resize guardrail reduces memory/CPU abuse.
- Human review for ambiguous compliance decisions.
- Production design would add malware scanning, authentication/authorization, encryption, audit logging, retention controls, rate limits, and formal ATO/FedRAMP-aligned hosting decisions.

## AI/ML modernization

The design creates a replaceable OCR interface. A future authorized vision model can be introduced without changing compliance rules or UI contracts. That keeps the deterministic regulatory logic separate from probabilistic extraction.
