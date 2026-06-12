---
name: humanizer
description: Post-processing style guide for reducing AI-detectable patterns in written text. Loaded by writing-helper Post-processing when pipeline_design declares post-process: humanize. Do not load from _index.md.
---

# humanizer

Post-processing style guide. Applied after writing-helper produces a draft,
before pdf-renderer converts to PDF. This is NOT round-trip translation —
it's a structured review pass that reduces template-like and predictable patterns.

**When to load:**
- `pipeline_design.md` declares `post-process: humanize` for the stage
- User requests at do-homework [B]: "降低一下 AI 味道" or similar

**When NOT to load:**
- Code files (code-writer output) — only applies to prose
- Unless user explicitly asks for code comment humanization

## Contract

- **reads:** `draft.md` (from writing-helper or manual input)
- **writes:** revised `draft.md` (in-place or as draft_revised.md)
- **preconditions:** draft text exists

## Guidance

Read the draft and revise for these patterns:

### Sentence structure variation

- Avoid uniform subject-verb-object rhythm throughout paragraphs
- Mix sentence lengths: some short (5-8 words), some medium (15-20), occasional longer ones
- Vary sentence openers — don't start every sentence with "The" or "This"

### Vocabulary diversity

- Avoid repeating the same academic filler phrases:
  "It is important to note that", "plays a crucial role", "has significant implications"
- Use specific language instead of hedging:
  "might potentially have an effect on" → "affects"
- Don't overuse "utilize" (use "use"), "facilitate" (use "enable" or "allow")

### Paragraph rhythm

- Vary paragraph lengths — not all paragraphs should be 4-5 sentences
- Some ideas can be a single-sentence paragraph for emphasis
- Don't end every paragraph with a summary sentence

### Reduce telltale AI patterns

- Remove meta-discourse: "In this section, I will discuss..." → just discuss it
- Remove redundant signposting: "As mentioned above", "As previously stated"
- Avoid numbered lists when prose would be more natural
- Don't over-qualify: "somewhat", "rather", "relatively" used excessively
- Replace generic conclusions with specific takeaways

### What NOT to change

- Factual content and citations — these stay exactly as written
- Technical terminology specific to the domain
- The actual arguments and their logical structure
- Required formatting (sections, headings, references)

## Self-check

- [ ] No paragraph starts with "It is important to note" or similar filler
- [ ] Sentence lengths vary across the text
- [ ] No excessive hedging ("might potentially somewhat")
- [ ] No meta-discourse ("In this section I will...")
- [ ] Citations and facts unchanged
- [ ] Word count within ±5% of original (not significantly shorter/longer)
