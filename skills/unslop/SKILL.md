---
name: unslop
description: Edit prose to remove unsupported, formulaic, or generic AI writing while preserving the author's intent and established voice. Use for marketing copy, PR and blog posts, articles, documentation, reports, messages, and other prose that needs a natural or less robotic edit. Do not use for code debugging or non-writing tasks.
---

# Unslop

Edit the text in context. Remove what weakens it without replacing the author's voice with a house style of your own.

## Preserve the contract

Before editing, identify what must survive:

- facts, numbers, claims, technical meaning, and domain terms;
- code, commands, identifiers, URLs, citations, and attribution;
- quotations and text marked as fixed or legally required;
- the author's uncertainty, confidence, opinion, humor, rhythm, and level of formality;
- the requested format, length, audience, and established house style.

Treat quoted material as read-only unless the user asks to edit the quotation itself. Keep citations attached to the claims they support. Do not strengthen a tentative claim, soften a firm conclusion, or replace a precise technical term merely because a simpler word exists.

Never invent facts, evidence, sources, opinions, personal experience, emotion, or measured results. Voice must come from the source text and user context. If the source has little personality, make it clear and specific rather than manufacturing a persona.

## Classify before editing

Use three severity tiers. A listed word or punctuation mark is evidence to inspect, not an automatic violation.

### Must fix

Remove or repair text that is unsupported, deceptive, or disconnected from the author's meaning:

- invented evidence, vague authority, or claims the source cannot support;
- generic praise presented as fact, such as "groundbreaking" without evidence;
- chatbot residue addressed to the requester rather than the intended reader;
- filler that changes no meaning;
- rewrites that alter facts, uncertainty, attribution, technical meaning, or the author's conclusion.

When a claim needs evidence and no source is available, narrow or remove the claim. Do not make up support.

### Usually review

Review these patterns in context and change them only when they make the passage less specific, less direct, or less like its author:

- stock transitions, canned conclusions, and promotional adjectives;
- abstract nouns where the sentence could name an action, owner, object, or result;
- inflated phrasing such as "serves as" when "is" carries the same meaning;
- repeated sentence shapes, forced groups, synonym cycling, and superficial `-ing` clauses;
- dense sentences, weak verbs propped up by adverbs, unnecessary hedging, and passive voice that hides a useful actor;
- heavy use of headings, bold labels, colons, parentheses, dashes, or other punctuation that creates a mechanical rhythm.

Words such as "crucial", "landscape", "leverage", and "robust" can be empty, but they can also be correct. Keep them when they carry the author's intended meaning or belong to the field's normal vocabulary. Judge dashes, semicolons, curly quotes, fragments, and long sentences by clarity and house style. Never replace punctuation only to satisfy a ban.

### Preserve deliberate choices

Leave a passage alone when the suspected tell is doing real work. Preserve:

- a repeated phrase used for emphasis;
- an em dash or fragment that matches the author's rhythm;
- formal or terse professional language suited to the audience;
- specialized vocabulary that is more precise than a plain substitute;
- parallel structure that makes instructions easier to scan;
- unusual wording, humor, or rough edges that mark the author's voice.

Do not force variation into text that is already clear. A light edit or no edit is a valid result.

## Edit

1. Map the preservation contract from the source and request.
2. Mark must-fix passages and contextual review candidates.
3. Make the smallest edits that solve those problems.
4. Read the result against the source. Confirm that every fact, quotation, citation, technical term, uncertainty marker, and deliberate style choice still has the same function.
5. Remove any opinion, evidence, emotion, or experience introduced by the edit rather than supported by the source.

Return the edited text in the requested format. Add an explanation only when the user asks for one or when a source conflict prevents a safe edit.

## Completion

Finish when the must-fix problems are gone, reviewed patterns either have a reason to remain or were improved, and a source-to-output check finds no change to the preservation contract. If the original already meets that bar, return it unchanged or with only the necessary correction.
