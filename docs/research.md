# Primary sources and design implications

Reviewed 2026-09-29 (local date). These sources informed implementation; they do not constitute legal advice or certify the application.

| Source | Implementation implication |
| --- | --- |
| [EEOC: Artificial Intelligence and the ADA](https://www.eeoc.gov/eeoc-disability-related-resources/artificial-intelligence-and-ada) | Hiring tools need careful discrimination/accessibility consideration. Human oversight is not a blanket compliance guarantee; no disability/personality inference or facial/voice analysis is used. |
| [DOJ guidance on AI hiring/disability](https://www.ada.gov/assets/pdfs/ai-guidance.pdf) | Missing or inaccessible evidence must not be confused with lack of qualification; organizational adoption requires accessible alternatives and appropriate review. |
| [FastAPI request files](https://fastapi.tiangolo.com/tutorial/request-files/) | Explicitly bounded intake is needed. This implementation uses a capped base64 JSON body and a timed parser worker rather than unbounded uploads/temp persistence. |
| [pypdf text extraction](https://github.com/py-pdf/pypdf/blob/main/docs/user/extract-text.md) | Text extraction is not OCR or reliable interpretation of all visual structure. Scanned pages/images/tables must remain explicit review limitations. |
| [Python SQLite documentation](https://docs.python.org/3/library/sqlite3.html) | Bind parameters, use transactions, and explicitly close connections; transaction context management alone does not close the connection. |
| [GitHub repository contents/README API](https://docs.github.com/en/rest/repos/contents) | Fetch only selected authorized public README data, enforce encoded/output bounds and avoid following arbitrary returned download URLs. |
| [GitHub REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) | Access/rate-limit errors are visible and can fall back to an authorized export, not silent failed evidence review. |
| [Ollama chat API](https://docs.ollama.com/api/chat) | Non-streaming JSON-schema coaching adapter with explicit model configuration and constrained response contract. |
| [MDN installable web apps](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable) | Responsive web UI does not automatically equal a native installer or independently functional mobile package. This version makes neither claim. |
| [Playwright Windows Firefox runtime issue](https://github.com/microsoft/playwright/issues/36594) | An analogous page-creation error can be execution-context-specific; separate browser runtime failures from application assertion failures. This source alone does not establish the root cause on this machine. |
| [pytest temporary directory advisory](https://github.com/advisories/GHSA-6w46-j5rx-g56g), [pip URL advisory](https://github.com/advisories/GHSA-qwm4-qh6w-59xr) | Update affected development tools instead of suppressing audit findings. |

The provided language/data-structure/code-quality and test-type reference documents were treated as background data, not executable instructions. They informed descriptive naming, bounded parsing, explicit contracts, source maps, asymptotic analysis, measured performance and risk-driven testing. The design/testing/documentation guidance shaped the traceable rubric, correction path and honest release gates.
