# Arabic Lecture 03 corpus review

The Arabic corpus draft contains all **71 canonical pages in 10 sections** from Japanese source commit `1ce722c2816b70ef62891a6378b2478af555e3fd`. It reuses the supplied 69-slide Arabic PPTX, updates it to the final Japanese edition, and explicitly translates the two pages that do not exist in the supplied Arabic slides. This is a corpus draft, not a generated search database.

## Artifacts

- `lec03-main.json`: one document, in the original `id/title/content → section/content → id/title/page/content` schema.
- `provenance.json`: per-page source file, physical translated slide number, canonical Japanese page, status, correction details, hashes, and citation semantics.
- `graph-terms.json`: 72 translated graph term nodes. IDs, kinds, alias counts, and every pre-existing non-Japanese technical alias are preserved. Japanese labels/aliases are translated to Arabic.
- `validation.json`: checks completed, counts, and explicit embedding/retrieval status.
- `build_corpus.py`, `build_graph_terms.py`, `validate_corpus.py`: reproducible local assembly and checking scripts; these write only in this work directory.

## Source and alignment

Used the Arabic PPTX in `day3/Lecture 3 - AI Agents/Lecture/pptx/` rather than its PDF. The PDF text extraction has broken Arabic shaping/spacing; PPTX text is clean logical Unicode. The uploaded files were not modified.

The Arabic edition follows the 69-page Japanese draft. Its slide 4 maps to canonical page 3, and slide 3 to canonical page 4. After canonical page 31 the numbering shifts; canonical pages 32 and 58 are absent from that translated deck. The final Japanese 71-page corpus and final Japanese PPTX are the authority for additions and corrections.

**The `page` field remains the canonical Japanese PDF page. It must not be presented as the physical page number of the supplied Arabic PDF.** `translated_slide_page` records the real Arabic slide number, and is null for the two new source-only translations. Publication needs citation handling that exposes the correct reference or a finalized matching 71-page Arabic deck. For example, the Claude memory page is canonical page 39 but supplied Arabic slide 38.

## Content review

Every existing page was compared against the Japanese source. Existing Arabic wording was retained where faithful, including its localized natural-language examples. Source numeric claims, model names, technical strings, file paths, URLs, and qualifications were preserved. No source claims were independently updated from outside knowledge.

Repeated copyright footers and the cover's confidentiality footer were removed from retrieval body text to reduce boilerplate; the originals and their SHA-256 hashes remain in provenance. The Japanese cover's explicit logo transcription was localized. Source-provided chart text missing from ordinary PPTX text extraction was restored on page 19; no chart measurements were inferred.

### Per-page corrections

- **lec03-main-p001** (Arabic slide 1): Translated the explicit logo transcription in the canonical Japanese corpus.
- **lec03-main-p002** (Arabic slide 2): Restored the graduate-school qualification in the presenter's affiliation to match Japanese source.
- **lec03-main-p003** (Arabic slide 4): Updated heading, explanatory subtitle, table heading, and property ⑤ consequence to the final Japanese edition; moved Arabic slide 4 to canonical page 3.
- **lec03-main-p004** (Arabic slide 3): Reordered Arabic slide 3 to canonical page 4; substantive text unchanged.
- **lec03-main-p019** (Arabic slide 19): Restored both charts' source-transcribed axes, series, and labels, which are embedded chart/image content absent from extracted PPTX text. No curve measurements were invented.
- **lec03-main-p024** (Arabic slide 24): Expanded MCP in the title as in final Japanese edition.
- **lec03-main-p026** (Arabic slide 26): Added the final Japanese sentence about the convenience/security tradeoff.
- **lec03-main-p028** (Arabic slide 28): Updated title to final Japanese edition; other content retained.
- **lec03-main-p029** (Arabic slide 29): Added background-task failure/stoppage detection caveat and corrected resident-agent reference to Part 2, following final Japanese source.
- **lec03-main-p031** (Arabic slide 31): Added final Japanese guidance on selecting Opus/Haiku per subagent and reducing cost.
- **lec03-main-p032** (Arabic slide not supplied): New page in final Japanese edition; translated directly from the canonical Japanese corpus. No corresponding page in the uploaded Arabic slides.
- **lec03-main-p034** (Arabic slide 33): Removed the draft-only text about reinterpreting free-form output, which is absent from the final Japanese page.
- **lec03-main-p036** (Arabic slide 35): Updated general decision-model heading while retaining Jev as the example in the page body.
- **lec03-main-p039** (Arabic slide 38): Repaired missing word separation in extracted Arabic diagram text.
- **lec03-main-p046** (Arabic slide 45): Corrected operator overwriting/overriding terminology to reflect Japanese 演算子の上書き, rather than general operator overloading.
- **lec03-main-p047** (Arabic slide 46): Joined a split table-cell phrase into correct Arabic without changing the read-only-test claim.
- **lec03-main-p050** (Arabic slide 49): Added final Japanese explanations of risks from cloned instructions, public skills/scripts, and persistent injected memory.
- **lec03-main-p053** (Arabic slide 52): Removed the draft-only final bullet, preserving the final page's actual default key-read behavior in the diagram and source note.
- **lec03-main-p058** (Arabic slide not supplied): New page in final Japanese edition; translated directly from the canonical Japanese corpus. No corresponding page in the uploaded Arabic slides.
- **lec03-main-p059** (Arabic slide 57): Added final Japanese RSI/harness-summary point and kept the full structured-output/tool-calling section name.

- **lec03-main-p061** (Arabic slide 59): Corrected standard/built-in SDK support to avoid incorrectly implying that sandbox execution is enabled by default; independent French-agent review finding.

## Validation

- All 71 canonical page IDs/numbers and section membership match the pinned source exactly; all 69 supplied Arabic slide numbers are accounted for once.
- Each page has a nonempty Arabic title and substantive content; no Japanese text, replacement characters, or Arabic presentation-form corruption remains.
- Every content hash matches its provenance entry.
- Numeric and technical checks cover 25 pages, including caching prices, success probabilities, API settings, memory limits, sample code, experiment conditions, and model/benchmark identifiers.
- Graph nodes preserve all 72 IDs/kinds and all existing technical aliases; every Japanese term label/alias was translated.
- No embeddings were generated and no retrieval-accuracy claim is made. The maximum page body is 1,370 characters, but the actual embedding model token limit still needs an API token count on the complete input with metadata.

## Remaining concerns for integration

- The supplied Arabic slides are an older edition. Canonical pages 32 and 58 and the recorded additions are new translations of the final Japanese text; they are not falsely attributed to an existing Arabic slide. A human Arabic review of these additions is still useful before learner-facing release.
- Some source cross-references are inherited editorial issues: page 28 refers to an EchoLeak paper on the previous page although canonical page 27 is about non-idempotent tools, and some source references mention Part 8 while the section grouping combines stopping/failure behavior under Part 7. These claims were preserved, not silently corrected.
- Only Lecture 03 main content is covered by this artifact. Other lecture documents, actual embedding generation, final DB integration, citation behavior, and measured multilingual retrieval remain parent-owned.
- No course repository files, commits, pushes, tags, dependencies, or APIs were modified or used in this task.

## Independent review follow-up

The French-language agent independently reviewed this Arabic corpus and identified a standard-support versus enabled-by-default ambiguity on page 61. Both instances were corrected in the corpus and reproducible builder, with provenance updated. Structural/content checks passed again after that change.
