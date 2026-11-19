# Arabic exercise corpus audit

Prepared 2026-11-19 from Japanese canonical source commit `1ce722c2816b70ef62891a6378b2478af555e3fd`. These are complete page translations for corpus preparation, not summaries and not generated embeddings.

## Coverage and sources

| Corpus | Pages | Arabic text characters | Longest page |
| --- | --- | --- | --- |
| `lec03-exercise.json` | 26/26 | 19,884 | 1,343 characters |
| `lec04-exercise.json` | 23/23 | 19,283 | 1,866 characters |

All page IDs, canonical page numbers and source section boundaries are retained. Titles and the section name are translated. All 49 pages are newly translated from Japanese: no Arabic exercise slide files were supplied, and no Arabic slide/PDF provenance is invented.

Canonical source text: `source-documents.json`. Japanese original files:

- `day3/第3回 演習・宿題：学習支援エージェントを作る.pptx` — final 26-slide presentation, with the original decomposed Unicode filename.
- `day4/第4回 演習・宿題：評価セットを作り、LLM に採点させる.pptx` — final 23-slide presentation.

Every source PPTX slide was checked against its canonical corpus page. The substantive text matches exactly after disregarding whitespace, presentation bullet markers and copyright. The separately supplied canonical visual transcriptions are also translated: lecture 3 cover logo; lecture 4 cover logo, annotation UI on page 14, and final logo on page 23. No untranslated or invented visual teaching content was added.

Each document has its own `-provenance.json`, with source commit, exact uploaded filename and file hash, canonical and actual Japanese slide numbers, slide XML member, source page hash, translated content hash, and explicit adaptations. Arabic source-file and physical Arabic slide/PDF page fields are null. The corpus `page` field refers to Japanese canonical pagination.

## Fidelity and deliberate localization

All instructional points, examples, caveats, tables, quantitative claims, model names, paths, flags and tool identifiers are retained. Layout-only line breaks were repaired, including shell commands and `sierra-research/tau2-bench`. Repeated copyright footers were omitted; author/date, logos and the cover disclosure sentence remain.

Existing Arabic course terminology was checked in `app/agent.py`, `app/tools.py`, `data/eval/rubric.md`, `tools/annotate.py` and `lectures/03/problem.md`. This establishes consistent tool descriptions, INSTRUCTIONS wording, rubric criterion names, the basic/applied/advanced level names, and actionable UI labels. It does not override Japanese source teaching content.

- Operational course-fetch URLs on page 13 of each document use `https://github.com/matsuolab/lecture-ai-engineering-2026-ar.git`, as authorized for the Arabic course workflow. `lec03-start`/`lec04-start`, branch names, shell flags and research/reference URLs are unchanged.
- Japanese `第N回` output-marker examples use the existing Arabic code's literal `Lecture NN` marker. This preserves the requirement that the lecture reference can be checked by code and avoids telling Arabic learners to emit a Japanese-only marker.
- Human-language example prompts, commit messages, comments and docstrings are translated; executable identifiers and syntax are unchanged. Source snippets that omit closing triple quotes remain explicitly identified as excerpts, not complete runnable replacements.
- UI action references use the current Arabic hesitation and save/next labels (`ترددت`, `احفظ وانتقل إلى التالي`). The source screenshot's explicit pass(1)/fail(0) labels remain source-image transcription; the current Arabic UI uses T/F. No claim is made that the supplied screenshot depicts the current Arabic UI.
- On lecture 4 page 16, expanded the source's abbreviated alternative fail-policy ellipsis into a full single-line Arabic rule. This makes both the pass and fail alternatives copyable without changing the policy or adding a new teaching claim.

## Content review

All 49 pages were reviewed against the Japanese content during translation, including:

- Lecture 3: 21-question comparison; `0.095 → 1.0`, `0 → 0.905`, 19/21 correct, no regressions, two residual failures; 14 training examples including four without evidence; fixed-seed/GPU reproducibility caveat; train/valid/test separation by paraphrase template; configuration, loss and overfitting caveats.
- Sync-fork and `Discard commits` warnings, safe alternate tagged-start instructions, conflict-abort instructions, own-fork PR direction and stopping Codespaces. These are material to students' workflow and were retained.
- Full displayed INSTRUCTIONS and docstring excerpt on lecture 3 page 16, including compulsory search, lecture-summary tool, no unsupported assertions, lecture marker, homework hints and the single-term-query rule.
- Tool registration and dummy-argument testing, `requires_approval=True`, `DeferredToolRequests`, output type, approval before execution, carrying `message_history`, and ignored personal logs. ADK/Pi scopes and the Pi behavior warning remain.
- Lecture 4: four criteria judged by LLM versus five human labels including the code-checked lecture marker. The source goal on page 10 still says four criteria; no silent rewrite conflates these counts.
- The `unsure` review route, coverage denominator, misses versus over-detection, and the fact that `--model test` is not a real evaluation remain explicit. Page 15 says clarity agreement is low, not that it is mathematically the lowest in the displayed example.
- Page 21 preserves SWE-bench Verified 500 tasks/93 developers/three validators per task; GPQA Diamond 198 four-choice questions and two other expert validators; Humanity's Last Exam 2,500 questions and two review rounds; both arXiv identifiers; and the restriction against pasting complete benchmark questions.

## Validation and limits

`build_exercise_corpora.py` reproducibly builds both documents and provenance from `exercise_translations.py` and the canonical sources. All structure, source mapping and content-hash checks pass. There are no remaining Japanese characters, replacement characters or corrupt Arabic presentation-form characters. Arabic remains in logical Unicode order.

A separate source Latin-token audit checked 323 page/token occurrences for lecture 3 and 199 for lecture 4. No technical omissions were found. Exceptions were reviewed and limited to translated prose words (`AI`, `fork`, `repo`, `secret`, `Web`), removed repetitive attribution tokens, and the explicitly authorized Arabic operational repository URL.

This is an editorial/source-fidelity check, not a claim of native-speaker review, measured retrieval accuracy, token-budget compatibility or embedding quality. Character lengths do not prove compliance with a model token limit. Full input coverage, actual token counting, embeddings and retrieval evaluation remain later stages. No API, DB build, course repository edit, commit, push or publication was performed.

## Independent second-agent review

The French corpus agent independently read all 49 Arabic exercise pages against Japanese and reported PASS with no material issue remaining. It verified final IDs, provenance hashes, technical/numeric/reference preservation and the expanded page-16 fail policy. Its offline check used the actual Arabic `_rule_based_judge` logic and real case 05: the original policy yields unsure, the copied pass rule yields pass, the copied fail rule yields fail, and a broken-line negative control yields unsure. No external API was used.

Reports: `../fr/independent-review-ar-exercises.md` and `../fr/independent-review-ar-exercises-validation.json`. Final reviewed corpus hashes:

```
lec03-exercise.json 281f01111d02db60ff48b5ac974a078ad4f906e7f1244a3f0031d9ec596b628c
lec04-exercise.json e93b201a7e361eff6405f381edd07dd7e3f14695ec9cafd38cbc89dfa42ad979
```
