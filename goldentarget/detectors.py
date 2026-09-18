"""Defect detection rules.

Every rule has the same shape: **resolve the entity against the authority, compare the row's claim
to what came back, and emit a finding only when they substantively disagree** — carrying the
authority's literal answer as proof.

Two invariants hold throughout, and together they are what keeps precision high:

1. *No authority answer, no finding.* If a lookup failed or the endpoint was unreachable, the row
   is left alone. Missing evidence costs recall, never precision.
2. *Cosmetic disagreement is normalized away, not reported.* Organism spelling, hyphenation and
   casing are reconciled in :mod:`goldentarget.normalize` before any comparison happens.

Nothing here is keyed to a specific gene, accession or value seen in the exam pack: each rule is a
procedure that queries the authority, so it behaves identically on the hidden pack.
"""

from . import authority as auth_mod
from . import normalize
from .findings import Finding

# Sources whose primary purpose is to assert an identity, ordered by how much weight their
# accession carries when arbitrating a conflict.
_MIN_TOKEN_PREFIX = 6


def _token_match(left, right):
    """Token equality that tolerates morphology: ``prostatectomy`` matches ``prostate``.

    Only applied to reasonably long tokens, where a shared 6-character prefix is meaningful rather
    than coincidental.
    """
    if left == right:
        return True
    if len(left) >= _MIN_TOKEN_PREFIX and len(right) >= _MIN_TOKEN_PREFIX:
        return left[:_MIN_TOKEN_PREFIX] == right[:_MIN_TOKEN_PREFIX]
    return False


def description_score(text, record):
    """How well the authority's description of ``record`` explains free-text ``text``.

    Matches are *tiered*, because not every kind of authority text identifies an entity equally
    well. A name is an identifier; a functional annotation is merely a description, and two
    unrelated proteins can easily share one. So a sentence token matching a recorded name or symbol
    counts for much more than the same token appearing somewhere in a comment. Without this, an
    ambiguous mention can tie on shared incidental vocabulary and be left unresolved.

    Returns ``(score, matched_tokens)``. Used only to choose between candidates the authority itself
    put forward for an alias — never to invent one.
    """
    text_tokens = [t for t in normalize.tokens(text) if len(t) > 2]
    if not text_tokens:
        return 0.0, []

    tiers = (
        # weight, tokens — names and symbols identify; keywords classify; comments only describe.
        (3.0, set(normalize.tokens(" ".join(record.all_names() + [record.gene] + list(record.gene_synonyms))))),
        (1.5, set(normalize.tokens(" ".join(record.keywords)))),
        (1.0, set(normalize.tokens(record.comment_text))),
    )

    total = 0.0
    matched = []
    for token in text_tokens:
        best = 0.0
        for weight, vocabulary in tiers:
            if weight <= best:
                continue
            for candidate in vocabulary:
                if _token_match(token, candidate):
                    best = weight
                    break
        if best > 0.0:
            total += best
            matched.append(token)
    # Normalised by the strongest possible score, so values stay comparable across sentences.
    return total / (3.0 * len(text_tokens)), sorted(set(matched))


def _canonical_for_row(authority, row):
    """The live entry a row's accession denotes, plus the hops taken to get there.

    Uses the same terminal resolver as clustering, so a detector and a golden record can never
    disagree about which target a row belongs to.
    """
    record = authority.record(row.accession)
    if record is None:
        return None, None, []
    _, hops, live = terminal_identity(authority, row, row.accession)
    return record, live, hops


MAX_HOPS = 6


def terminal_identity(authority, row, accession):
    """Follow an accession's lifecycle to the live entry it finally denotes.

    Obsolescence chains, and they are longer than one hop in real data: ``E9PGB9`` was merged into
    ``Q86YH7``, which was later merged into ``P56524`` (HDAC4). Reporting the first hop as the
    correction would hand back another dead accession, so every hop is walked to a live entry.

    Returns ``(final_accession, hops, final_record)``. ``hops`` is the audit trail, quoted in the
    finding so the correction can be checked by hand. Demerges are resolved by the row's own gene
    symbol at each step, since only the row knows which side of the split it meant.
    """
    current = normalize.upper(accession)
    hops = []
    seen = {current}
    for _ in range(MAX_HOPS):
        record = authority.record(current)
        if record is None or not record.known or record.status == auth_mod.STATUS_ACTIVE:
            return current, hops, record

        if record.status == auth_mod.STATUS_SECONDARY and record.primary:
            nxt = normalize.upper(record.primary)
            hops.append("%s is secondary to %s" % (current, nxt))
        elif record.status in (auth_mod.STATUS_MERGED, auth_mod.STATUS_DEMERGED) and record.merge_targets:
            targets = [normalize.upper(t) for t in record.merge_targets if t]
            chosen, _ = _choose_merge_target(authority, row, record, targets)
            if not chosen:
                return current, hops, record
            nxt = chosen
            hops.append("%s was %s into %s" % (current, record.inactive_reason or record.status.upper(), nxt))
        else:
            return current, hops, record  # DELETED with no successor

        if nxt in seen:
            return current, hops, record  # defensive: never loop on a cyclic chain
        seen.add(nxt)
        current = nxt
    return current, hops, authority.record(current)


# --------------------------------------------------------------------------- accession lifecycle


def detect_accession_status(authority, rows):
    """Accessions that are obsolete, secondary, or unknown to the authority.

    The EBI Proteins API cannot distinguish "never existed" from "no longer current", so anything
    it does not return is escalated to UniProt REST, which reports ``inactiveReason`` (MERGED /
    DEMERGED / DELETED) together with the accession(s) the entry became. A demerge is genuinely
    ambiguous — one accession split into several — so the row's own gene symbol is used to pick
    which side of the split it meant, and the choice is spelled out in the finding.
    """
    findings = []
    for row in rows:
        raw = row.accession
        if not raw:
            continue
        record = authority.record(raw)
        if record is None or not record.known:
            continue  # invariant 1: unreachable or unresolvable, so make no claim

        if record.status == auth_mod.STATUS_ACTIVE:
            continue

        if record.status == auth_mod.STATUS_SECONDARY and record.primary:
            findings.append(Finding(
                gene=record.gene or row.gene_symbol,
                observed=raw,
                correct=record.primary,
                retrieved_evidence=record.evidence,
                evidence_source=record.evidence_source,
                classification="secondary_accession",
                field="accession",
                reasoning=(
                    "%s is a secondary accession: UniProt resolves it to primary accession %s "
                    "(entry %s). It still dereferences today, so the identity is right and only "
                    "the key is stale." % (raw, record.primary, record.entry_name or "?")
                ),
                impact="Stale-but-valid key: exact-match joins against current UniProt keys miss this row.",
                locations=[row.locator()],
                source_files=[row.source_file_stem()],
            ))
            continue

        if record.status in (auth_mod.STATUS_MERGED, auth_mod.STATUS_DEMERGED, auth_mod.STATUS_DELETED):
            targets = [normalize.upper(t) for t in record.merge_targets if t]
            chosen, reason = _choose_merge_target(authority, row, record, targets)
            if not chosen:
                continue  # DELETED with no successor: nothing to correct it to, so stay silent
            final, hops, live = terminal_identity(authority, row, raw)
            if not final or final == raw:
                continue
            evidence = record.evidence
            if live is not None and live.known:
                evidence = "%s ; resolved to live entry %s -> %s" % (record.evidence, final, live.evidence)
            chain_note = ("Chain: %s. " % "; ".join(hops)) if len(hops) > 1 else ""
            findings.append(Finding(
                gene=(live.gene if live is not None and live.gene else row.gene_symbol),
                observed=raw,
                correct=final,
                retrieved_evidence=evidence,
                evidence_source=record.evidence_source,
                classification="obsolete_accession",
                field="accession",
                reasoning=(
                    "UniProt reports %s as %s%s. %s" % (
                        raw, record.inactive_reason or record.status.upper(),
                        (" into " + ", ".join(targets)) if targets else "",
                        chain_note or reason,
                    )
                ),
                impact=(
                    "Dead key: the row survives as a phantom target and splits one real entity "
                    "across two master records."
                ),
                locations=[row.locator()],
                source_files=[row.source_file_stem()],
            ))
    return findings


def _choose_merge_target(authority, row, record, targets):
    """Pick which successor accession a merged/demerged row meant, using the row's own symbol."""
    if not targets:
        return "", ""
    if len(targets) == 1:
        return targets[0], "Its content now lives under %s." % targets[0]

    # A demerge splits one accession into several distinct entries. The row's gene symbol says
    # which of them it was actually describing.
    claimed = normalize.upper(row.gene_symbol)
    for target in targets:
        candidate = authority.record(target)
        if candidate is not None and candidate.known and claimed and claimed in candidate.all_symbols():
            return target, (
                "The entry was demerged into %s; the row's own gene symbol %s matches %s "
                "(approved symbol %s), so that is the side of the split it denotes."
                % (", ".join(targets), row.gene_symbol, target, candidate.gene or "?")
            )
    claimed_name = row.protein_name
    if claimed_name:
        best, best_score = "", 0.0
        for target in targets:
            candidate = authority.record(target)
            if candidate is None or not candidate.known:
                continue
            score, _ = description_score(claimed_name, candidate)
            if score > best_score:
                best, best_score = target, score
        if best and best_score >= 0.5:
            return best, (
                "The entry was demerged into %s; the row's protein name matches %s most closely."
                % (", ".join(targets), best)
            )
    return "", ""


# --------------------------------------------------------------------------- invalid accessions


def detect_invalid_accession(authority, rows):
    """Accession values that are not accessions, or that the authority does not know.

    A transposed or truncated accession is internally consistent — it looks like a key and joins to
    nothing — so only the authority can expose it. Repairing it needs a second, independent route to
    the same entity, and the row supplies one: its gene symbol. When the authority returns exactly
    one reviewed entry for that symbol in the row's organism, that entry *is* the correction. When it
    returns several, or none, we say nothing rather than guess.
    """
    findings = []
    for row in rows:
        raw = row.accession
        if not raw:
            continue
        malformed = not normalize.looks_like_accession(raw)
        record = authority.record(raw)
        unknown = record is not None and not record.known
        if not malformed and not unknown:
            continue
        if not malformed and record is None:
            continue  # never resolved (e.g. deadline hit): no evidence, so no claim

        symbol = normalize.upper(row.gene_symbol)
        if not symbol:
            continue
        tax_hint = row.get("tax_id") or None
        candidates = [
            candidate for candidate in authority.find_by_symbol(symbol, tax_hint)
            if candidate.primary and normalize.upper(candidate.gene) == symbol
        ]
        if len(candidates) != 1:
            continue  # cannot single out one entity, so no correction can be proven
        candidate = candidates[0]

        findings.append(Finding(
            gene=candidate.gene,
            observed=raw,
            correct=candidate.primary,
            retrieved_evidence="%s ; the authority returns no entry for %r%s" % (
                candidate.evidence, raw,
                " and it does not match the UniProtKB accession format" if malformed else "",
            ),
            evidence_source=candidate.evidence_source,
            classification="invalid_accession",
            field="accession",
            reasoning=(
                "%r does not resolve to any entry%s. The row's gene symbol %s resolves to exactly "
                "one reviewed entry, %s (%s), which is the accession this row should carry."
                % (
                    raw,
                    " and is not a well-formed UniProtKB accession" if malformed else "",
                    row.gene_symbol, candidate.primary, candidate.entry_name or "?",
                )
            ),
            impact=(
                "Unresolvable key: the row joins to nothing, so the target is invisible to every "
                "accession-keyed downstream system."
            ),
            locations=[row.locator()],
            source_files=[row.source_file_stem()],
        ))
    return findings


# --------------------------------------------------------------------------- isoform granularity


def detect_isoform_accession(authority, rows):
    """Rows keyed on a splice isoform instead of the protein entry.

    ``Q13422-3`` is a perfectly valid UniProt identifier, which is exactly why this defect is
    invisible without the authority: the row looks internally consistent (its ``entry_name`` even
    says ``IKZF1_HUMAN``) and the identifier dereferences. But a target master holds one record per
    protein, not one per splice variant, so keying a target on an isoform silently changes what the
    record *means* — and if another source uses the parent accession, the master ends up with two
    records for one target.

    The proof is the parent entry's own ``ALTERNATIVE_PRODUCTS`` annotation, which lists its isoform
    identifiers. We only report when the authority confirms the row's value is a listed isoform of
    the parent; a bare guess from the string shape would not be evidence.
    """
    findings = []
    for row in rows:
        raw = normalize.upper(row.accession)
        if not raw:
            continue
        split = normalize.split_isoform(raw)
        if not split:
            continue
        parent_accession, isoform_number = split
        parent = authority.record(parent_accession)
        if parent is None or not parent.is_live:
            continue
        if raw not in parent.isoform_ids:
            continue  # the authority does not confirm this isoform: make no claim

        isoform_name = parent.isoform_ids.get(raw) or isoform_number
        findings.append(Finding(
            gene=parent.gene or row.gene_symbol,
            observed=row.accession,
            correct=parent.primary,
            retrieved_evidence="%s ; the entry's ALTERNATIVE_PRODUCTS annotation lists isoforms %s, "
                               "so %s is isoform %s of %s rather than a protein entry" % (
                                   parent.evidence, ", ".join(sorted(parent.isoform_ids)),
                                   raw, isoform_name, parent.primary,
                               ),
            evidence_source=parent.evidence_source,
            classification="isoform_accession",
            field="accession",
            reasoning=(
                "%s is a splice-isoform identifier, not a primary accession: the authority lists it "
                "as isoform %s of %s (%s, %s). A target master keys one record per protein, so this "
                "row should carry %s." % (
                    row.accession, isoform_name, parent.primary, parent.gene or "?",
                    parent.entry_name or "?", parent.primary,
                )
            ),
            impact=(
                "Wrong granularity: the target is keyed to one splice variant, so assay data for the "
                "protein splits by isoform and no record represents the target itself."
            ),
            locations=[row.locator()],
            source_files=[row.source_file_stem()],
        ))
    return findings


# --------------------------------------------------------------------------- organism


def detect_organism(authority, rows):
    """Rows whose stated organism contradicts the organism the accession actually belongs to.

    Every spelling the extracts use for one organism (``Homo sapiens``, ``H. sapiens``, ``human``,
    ``Homo sapiens (Human)``) is reconciled first, and an explicit matching ``tax_id`` settles the
    question outright. Only a genuine cross-species mapping survives to become a finding.
    """
    findings = []
    for row in rows:
        claimed = row.get("organism")
        claimed_tax = row.get("tax_id")
        if not claimed and not claimed_tax:
            continue
        _, live, _ = _canonical_for_row(authority, row)
        if live is None or not live.is_live or not live.scientific_name:
            continue

        if normalize.organism_matches(
            claimed, live.scientific_name, live.common_names, live.tax_id, claimed_tax
        ):
            continue

        observed = claimed or claimed_tax
        findings.append(Finding(
            gene=live.gene or row.gene_symbol,
            observed=observed,
            correct=live.organism_label() or live.scientific_name,
            retrieved_evidence=live.evidence,
            evidence_source=live.evidence_source,
            classification="organism_mismatch",
            field="organism",
            reasoning=(
                "The row states organism %r for accession %s, but the authority returns %s "
                "(taxon %s) for that accession. This is a cross-species mismatch, not a spelling "
                "difference." % (observed, row.accession, live.scientific_name, live.tax_id or "?")
            ),
            impact="Wrong mapping: species-specific pharmacology and assay data attach to the wrong orthologue.",
            locations=[row.locator()],
            source_files=[row.source_file_stem()],
        ))

        if claimed_tax and live.tax_id and str(claimed_tax) != str(live.tax_id):
            findings.append(Finding(
                gene=live.gene or row.gene_symbol,
                observed=str(claimed_tax),
                correct=str(live.tax_id),
                retrieved_evidence=live.evidence,
                evidence_source=live.evidence_source,
                classification="organism_mismatch",
                field="tax_id",
                reasoning="The row's tax_id %s disagrees with the authority's taxon %s for %s."
                          % (claimed_tax, live.tax_id, row.accession),
                impact="Wrong mapping: the taxonomy key contradicts the accession's true organism.",
                locations=[row.locator()],
                source_files=[row.source_file_stem()],
            ))
    return findings


# --------------------------------------------------------------------------- symbol vs accession


def detect_symbol(authority, rows):
    """Gene symbols that disagree with the accession sitting next to them.

    Three genuinely different problems hide behind one symptom, and separating them is the whole
    job here:

    * the symbol is a **former** name the authority still lists as a synonym — stale but valid,
      low severity, the accession is fine;
    * the symbol is right and the **accession** points at a different protein — a wrong mapping,
      high severity, and the value that needs correcting is the accession;
    * the accession is right and the **symbol** belongs to something else — also high severity, but
      the value that needs correcting is the symbol.

    They are told apart by arbitration: the row's own protein-name field is a third, independent
    witness, so whichever of the two keys it corroborates is the one that is right. Only when that
    witness is silent do we fall back to trusting the accession, because it is the machine key.
    """
    findings = []
    for row in rows:
        record, live, _ = _canonical_for_row(authority, row)
        if live is None or not live.is_live:
            continue
        claimed = normalize.upper(row.gene_symbol)
        approved = live.gene
        if not approved:
            continue

        if not claimed:
            findings.append(Finding(
                gene=approved,
                observed="(empty gene_symbol)",
                correct=approved,
                retrieved_evidence=live.evidence,
                evidence_source=live.evidence_source,
                classification="missing_gene_symbol",
                field="gene_symbol",
                reasoning=(
                    "The row registers accession %s with no gene symbol. The authority gives the "
                    "approved symbol as %s (entry %s)." % (row.accession, approved, live.entry_name or "?")
                ),
                impact="Incomplete record: the golden record cannot be keyed by gene until this is filled.",
                locations=[row.locator()],
                source_files=[row.source_file_stem()],
            ))
            continue

        if claimed == normalize.upper(approved):
            continue

        symbols = live.all_symbols()
        if claimed in symbols:
            # The authority itself still lists this name for this entry: a previous official
            # symbol in continued use. The identity is correct, so this is a label problem.
            findings.append(Finding(
                gene=approved,
                observed=row.gene_symbol,
                correct=approved,
                retrieved_evidence=live.evidence,
                evidence_source=live.evidence_source,
                classification="stale_gene_symbol",
                field="gene_symbol",
                reasoning=(
                    "%s is listed by the authority as a synonym of %s (entry %s), not its approved "
                    "symbol. The accession %s is correct, so this is a stale label rather than a "
                    "wrong mapping." % (row.gene_symbol, approved, live.entry_name or "?", row.accession)
                ),
                impact="Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.",
                locations=[row.locator()],
                source_files=[row.source_file_stem()],
            ))
            continue

        # The symbol is not one this entry answers to. Ask the authority which entry does.
        alternatives = [
            candidate for candidate in authority.find_by_symbol(claimed, live.tax_id or None)
            if normalize.upper(candidate.gene) == claimed and candidate.primary != live.primary
        ]

        name = row.protein_name
        name_backs_accession = any(normalize.names_agree(name, n) for n in live.all_names()) if name else False
        name_backs_alternative = False
        best_alternative = None
        for candidate in alternatives:
            if name and any(normalize.names_agree(name, n) for n in candidate.all_names()):
                name_backs_alternative = True
                best_alternative = candidate
                break
        if best_alternative is None and alternatives:
            best_alternative = alternatives[0]
        # BindingDB-style rows often restate the symbol as the target name ("KISS1", "KISS1
        # protein", "IGLV1-47 protein"); that still counts as the name backing the symbol rather
        # than the accession. Compared on slugs so hyphenated symbols behave like any other.
        symbol_slug = normalize.slug(row.gene_symbol)
        name_slug = normalize.slug(name)
        name_restates_symbol = bool(symbol_slug) and bool(name_slug) and (
            name_slug == symbol_slug
            or name_slug.startswith(symbol_slug + " ")
            or name_slug.endswith(" " + symbol_slug)
        )

        if name_backs_accession and not name_backs_alternative:
            findings.append(Finding(
                gene=approved,
                observed=row.gene_symbol,
                correct=approved,
                retrieved_evidence=live.evidence,
                evidence_source=live.evidence_source,
                classification="wrong_gene_symbol",
                field="gene_symbol",
                reasoning=(
                    "Accession %s is %s (%s) per the authority, and the row's own protein name %r "
                    "matches that entry. The gene symbol %s is therefore the incorrect field."
                    % (row.accession, approved, live.entry_name or "?", name, row.gene_symbol)
                ),
                impact="Wrong mapping: the row asserts a gene that does not own this accession.",
                locations=[row.locator()],
                source_files=[row.source_file_stem()],
            ))
            continue

        if best_alternative is not None and (name_backs_alternative or name_restates_symbol):
            findings.append(Finding(
                gene=claimed,
                observed=row.accession,
                correct=best_alternative.primary,
                retrieved_evidence="%s ; queried accession resolves instead to %s" % (
                    best_alternative.evidence, live.evidence,
                ),
                evidence_source=best_alternative.evidence_source,
                classification="wrong_accession_mapping",
                field="accession",
                reasoning=(
                    "The row's gene symbol %s and protein name %r both denote %s (%s), but the "
                    "accession recorded is %s, which the authority resolves to a different protein "
                    "(%s, %s). Two of the row's three identity fields agree, so the accession is "
                    "the defective one." % (
                        row.gene_symbol, name, best_alternative.primary,
                        best_alternative.entry_name or "?", row.accession,
                        approved, live.entry_name or "?",
                    )
                ),
                impact=(
                    "Wrong mapping — the most damaging class: every assay and publication on this "
                    "row attaches to the wrong protein in the master."
                ),
                locations=[row.locator()],
                source_files=[row.source_file_stem()],
            ))
            continue

        if best_alternative is not None:
            # The name field is silent or ambiguous. The accession is the machine key and the more
            # reliable of the two, so the symbol is reported as the defective value.
            findings.append(Finding(
                gene=approved,
                observed=row.gene_symbol,
                correct=approved,
                retrieved_evidence="%s ; symbol %s belongs to %s" % (
                    live.evidence, row.gene_symbol, best_alternative.primary,
                ),
                evidence_source=live.evidence_source,
                classification="wrong_gene_symbol",
                field="gene_symbol",
                reasoning=(
                    "Accession %s is %s per the authority, while the symbol %s belongs to a "
                    "different entry (%s). The row's protein name does not corroborate either "
                    "side, so the accession is trusted as the stronger key."
                    % (row.accession, approved, row.gene_symbol, best_alternative.primary)
                ),
                impact="Wrong mapping: gene and accession in this row denote different proteins.",
                locations=[row.locator()],
                source_files=[row.source_file_stem()],
            ))
            continue

        # No entry anywhere answers to this symbol: an unrecognised label on an otherwise sound row.
        findings.append(Finding(
            gene=approved,
            observed=row.gene_symbol,
            correct=approved,
            retrieved_evidence=live.evidence,
            evidence_source=live.evidence_source,
            classification="unknown_gene_symbol",
            field="gene_symbol",
            reasoning=(
                "%s is neither the approved symbol nor a recorded synonym of %s, and the authority "
                "returns no entry for it in this organism. The approved symbol for the row's "
                "accession is %s." % (row.gene_symbol, row.accession, approved)
            ),
            impact="Unrecognised label: blocks symbol-based lookup of a target that is otherwise sound.",
            locations=[row.locator()],
            source_files=[row.source_file_stem()],
        ))
    return findings


# --------------------------------------------------------------------------- cross-references


def detect_crossreferences(authority, rows):
    """External database identifiers that point at a different entry than the row's accession.

    UniProt curates its own cross-references, so a ChEMBL target id is checkable in both
    directions: the accession's ``ChEMBL`` cross-reference list, and a reverse ``xref:chembl-...``
    search. When the row's accession and its ChEMBL id disagree about which protein they describe,
    the authority arbitrates — and it is the only witness that can.
    """
    findings = []
    for row in rows:
        external = row.get("chembl_id") or row.get("external_id")
        if not external or not external.upper().startswith("CHEMBL"):
            continue
        _, live, _ = _canonical_for_row(authority, row)
        if live is None or not live.is_live:
            continue

        listed = {value.upper() for value in live.xrefs.get("ChEMBL", ())}
        if external.upper() in listed:
            continue
        if not listed:
            continue  # authority records no ChEMBL cross-reference at all: nothing to contradict

        owners = authority.find_by_xref("chembl", external)
        owners = [owner for owner in owners if owner.primary]
        if not owners:
            continue  # cannot prove the id belongs elsewhere, so make no claim
        owner = owners[0]
        if owner.primary == live.primary:
            continue

        # Which field is wrong? The row's own gene symbol and protein name decide.
        claimed_symbol = normalize.upper(row.gene_symbol)
        accession_backed = claimed_symbol and claimed_symbol in live.all_symbols()
        if accession_backed:
            # Accession and symbol agree with each other, so the external id is the odd one out.
            correct_id = sorted(listed)[0]
            findings.append(Finding(
                gene=live.gene or row.gene_symbol,
                observed=external,
                correct=correct_id,
                retrieved_evidence="%s ; UniProt lists ChEMBL cross-reference(s) %s for %s, while "
                                   "%s belongs to %s (%s)" % (
                                       live.evidence, ",".join(sorted(listed)), live.primary,
                                       external, owner.primary, owner.entry_name or "?",
                                   ),
                evidence_source=owner.evidence_source,
                classification="wrong_crossreference",
                field="chembl_id" if row.get("chembl_id") else "external_id",
                reasoning=(
                    "The row describes %s (%s, confirmed by its own gene symbol), but carries "
                    "ChEMBL id %s, which UniProt cross-references to %s (%s). The correct ChEMBL "
                    "id for this target is %s." % (
                        live.primary, live.gene or "?", external, owner.primary,
                        owner.entry_name or "?", correct_id,
                    )
                ),
                impact="Broken join: downstream lookups by ChEMBL id retrieve a different target.",
                locations=[row.locator()],
                source_files=[row.source_file_stem()],
            ))
        else:
            findings.append(Finding(
                gene=owner.gene or row.gene_symbol,
                observed=row.accession,
                correct=owner.primary,
                retrieved_evidence="%s ; UniProt maps ChEMBL id %s to %s, not to %s (%s)" % (
                    owner.evidence, external, owner.primary, live.primary, live.gene or "?",
                ),
                evidence_source=owner.evidence_source,
                classification="wrong_accession_mapping",
                field="accession",
                reasoning=(
                    "ChEMBL id %s is cross-referenced by UniProt to %s (%s), but this row pairs it "
                    "with accession %s (%s)." % (
                        external, owner.primary, owner.entry_name or "?", row.accession,
                        live.gene or "?",
                    )
                ),
                impact="Wrong mapping: the accession contradicts the curated cross-reference.",
                locations=[row.locator()],
                source_files=[row.source_file_stem()],
            ))
    return findings


# --------------------------------------------------------------------------- duplicate identity


def detect_duplicates(authority, rows, clusters, explained=()):
    """One real target carrying more than one identity in the pack.

    Two distinct shapes, both classic master-data failures:

    * two different accessions in the pack that the authority collapses onto the same live entry —
      the master would otherwise hold two golden records for one protein;
    * two internal registrations of the same target under different internal ids — the registry
      itself has duplicated the entity.

    ``explained`` lists accessions whose duplication the lifecycle detector has already diagnosed
    (they are obsolete or secondary). Reporting those a second time here would be crying wolf about
    a defect already carrying a correction, so they are annotated on that finding instead.
    """
    findings = []
    explained = {normalize.upper(value) for value in explained}
    for accession, cluster in sorted(clusters.items()):
        live = cluster.get("record")
        raw_accessions = sorted(cluster.get("raw_accessions", ()))
        if live is None or not live.known or len(raw_accessions) < 2:
            continue
        redundant = [value for value in raw_accessions if value != accession and value not in explained]
        if not redundant:
            continue
        for value in redundant:
            record = authority.record(value)
            if record is None or not record.known:
                continue
            evidence = "%s ; %s and %s both resolve to the single live entry %s (%s)" % (
                record.evidence, value, accession, accession, live.entry_name or "?",
            )
            findings.append(Finding(
                gene=live.gene or "",
                observed="%s (alongside %s for the same target)" % (value, accession),
                correct=accession,
                retrieved_evidence=evidence,
                evidence_source=record.evidence_source,
                classification="duplicate_identity",
                field="accession",
                reasoning=(
                    "The pack registers this target under %d accessions (%s). The authority "
                    "resolves all of them to %s, so %s is a duplicate identity for a target that "
                    "already has a record." % (
                        len(raw_accessions), ", ".join(raw_accessions), accession, value,
                    )
                ),
                impact=(
                    "Duplicate identity: assays and literature split across two master records for "
                    "one protein, so neither record is complete."
                ),
                locations=sorted(cluster.get("locations_by_accession", {}).get(value, ())),
                source_files=sorted(cluster.get("sources_by_accession", {}).get(value, ())),
            ))

    by_target = {}
    for row in rows:
        if row.source != "internal":
            continue
        _, live, _ = _canonical_for_row(authority, row)
        if live is None or not live.is_live:
            continue
        by_target.setdefault(live.primary, []).append(row)
    for accession, group in sorted(by_target.items()):
        ids = sorted({row.record_id for row in group})
        if len(ids) < 2:
            continue
        live = authority.record(accession)
        if live is None:
            continue
        findings.append(Finding(
            gene=live.gene or group[0].gene_symbol,
            observed=", ".join(ids),
            correct=ids[0],
            retrieved_evidence="%s ; all %d internal registrations resolve to the one live entry %s"
                               % (live.evidence, len(ids), accession),
            evidence_source=live.evidence_source,
            classification="duplicate_registration",
            field="internal_id",
            reasoning=(
                "Internal registry rows %s all resolve to %s (%s). One real target holds several "
                "internal ids; %s is the earliest and should be retained as the survivor."
                % (", ".join(ids), accession, live.gene or "?", ids[0])
            ),
            impact="Duplicate identity inside the registry: programme data fragments across internal ids.",
            locations=sorted(row.locator() for row in group),
            source_files=["source_internal"],
        ))
    return findings


# --------------------------------------------------------------------------- literature mentions


def detect_ambiguous_mentions(authority, publication_rows, clusters, default_tax_id=None):
    """Literature mentions that name an alias shared by more than one protein.

    A mention is only worth resolving when it is *not* the approved symbol of exactly one target in
    the pack. For those, the authority is asked which entries legitimately answer to the alias (as
    approved symbol, synonym or short name) and the row's ``context_sentence`` decides between them,
    scored against each candidate's authoritative names, keywords and functional annotation.

    The ``pmid`` column is never fetched and never flagged: those are internal reference numbers,
    and some collide with unrelated real PubMed records, so any paper behind them is an artifact of
    the synthetic numbering rather than evidence about the row.
    """
    findings = []
    approved_index = {}
    for accession, cluster in clusters.items():
        live = cluster.get("record")
        if live is None or not live.gene:
            continue
        approved_index.setdefault(normalize.upper(live.gene), set()).add(accession)

    in_pack = set(clusters.keys())

    for row in publication_rows:
        mention = row.gene_symbol
        sentence = row.get("context")
        if not mention or not sentence:
            continue
        key = normalize.upper(mention)
        owners = approved_index.get(key, set())
        if len(owners) == 1:
            continue  # unambiguous: exactly one target in the pack owns this symbol

        candidates = [
            candidate for candidate in authority.find_by_alias(key, default_tax_id)
            if candidate.primary and key in candidate.all_symbols()
        ]
        if len(owners) > 1:
            for accession in owners:
                record = clusters[accession].get("record")
                if record is not None and all(c.primary != accession for c in candidates):
                    candidates.append(record)
        # Prefer candidates the pack actually contains; a target absent from all five extracts is
        # not what this row is about.
        scoped = [candidate for candidate in candidates if candidate.primary in in_pack]
        candidates = scoped or candidates
        # The search endpoint returns a thin projection (no keywords, no functional annotation).
        # Swap in the fully-resolved record wherever we already have one, so disambiguation sees
        # everything the authority knows rather than just names.
        upgraded = []
        for candidate in candidates:
            full = authority.record(candidate.primary)
            upgraded.append(full if (full is not None and full.is_live and full.keywords) else candidate)
        candidates = upgraded
        if len(candidates) < 2:
            continue  # not actually ambiguous, or the authority cannot ground it

        scored = []
        for candidate in candidates:
            score, matched = description_score(sentence, candidate)
            scored.append((score, len(matched), candidate, matched))
        scored.sort(key=lambda item: (-item[0], -item[1], item[2].primary))
        best_score, _, best, matched = scored[0]
        runner_up = scored[1][0] if len(scored) > 1 else 0.0
        # A decisive *relative* margin, so the test does not depend on sentence length: the winner
        # must explain the sentence at least half again as well as its nearest rival. An even split
        # means the sentence genuinely does not disambiguate, and guessing there would cost
        # precision for no gain.
        if best_score <= 0.0:
            continue
        if runner_up > 0.0 and best_score / runner_up < 1.5:
            continue
        if normalize.upper(best.gene) == key:
            continue

        findings.append(Finding(
            gene=best.gene,
            observed=mention,
            correct=best.gene,
            retrieved_evidence="%s ; alias %r is shared by %s, and the authority's description of "
                               "%s matches the context sentence on %s" % (
                                   best.evidence, mention,
                                   ", ".join("%s=%s" % (c.primary, c.gene or "?") for _, _, c, _ in scored),
                                   best.primary, ", ".join(matched) or "its recorded names",
                               ),
            evidence_source=best.evidence_source,
            classification="ambiguous_mention",
            field="target_mention",
            reasoning=(
                "%r is not the approved symbol of a single target: the authority shows it is "
                "shared by %s. The context sentence %r describes %s (%s, %s), so this mention "
                "resolves to %s." % (
                    mention,
                    " and ".join("%s (%s)" % (c.gene or "?", c.primary) for _, _, c, _ in scored),
                    sentence, best.gene, best.primary, best.protein_name or "?", best.gene,
                )
            ),
            impact=(
                "Ambiguous mention: attributing this publication to the wrong gene mis-assigns "
                "literature evidence between two unrelated proteins."
            ),
            locations=[row.locator()],
            source_files=["source_publications"],
        ))
    return findings
