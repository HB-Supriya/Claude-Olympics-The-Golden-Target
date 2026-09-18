"""String normalization shared by every detector.

The single most important precision decision in this tool lives here: telling *cosmetic*
disagreement apart from *substantive* disagreement. The extracts spell the same organism four ways
(``Homo sapiens`` / ``H. sapiens`` / ``human`` / ``Homo sapiens (Human)``) and the same protein
name with different hyphenation and casing. None of that is a data-quality defect, and flagging it
would burn precision. So all of it is normalized away here, and only what survives normalization is
allowed to become a finding.
"""

import re

_WS = re.compile(r"\s+")
_PARENTHETICAL = re.compile(r"\s*\([^)]*\)")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")

ACCESSION_RE = re.compile(
    r"^(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})$"
)
# UniProt names a specific splice variant as <accession>-<n>. It is a valid identifier, but it
# identifies an isoform rather than a protein entry, so it is never a target's primary accession.
ISOFORM_RE = re.compile(r"^(.+)-([0-9]+)$")

# Stop words that carry no discriminating power when matching a protein description.
_STOPWORDS = frozenset("""
a an and as at be been by for from had has have in into is it its of on or that the this to was
were with which protein human isoform putative probable uncharacterized family member type
""".split())


def squash(value):
    return _WS.sub(" ", (value or "").strip())


def upper(value):
    return squash(value).upper()


def strip_parenthetical(value):
    return squash(_PARENTHETICAL.sub("", value or ""))


def slug(value):
    """Casefolded, punctuation-free form: makes ``Prostate specific antigen`` ==
    ``Prostate-specific antigen`` so hyphenation differences never become findings."""
    return _NON_ALNUM.sub(" ", (value or "").lower()).strip()


def tokens(value):
    return [tok for tok in slug(value).split() if tok and tok not in _STOPWORDS]


def looks_like_accession(value):
    """True for strings matching the official UniProtKB accession grammar."""
    return bool(ACCESSION_RE.match(upper(value)))


def split_isoform(value):
    """``Q13422-3`` -> ``('Q13422', '3')``; anything else -> ``None``.

    An isoform identifier is *valid* but has the wrong granularity for a target master: the master
    holds one record per protein, not one per splice variant. Recognising the form lets us resolve
    the row to its parent entry instead of discarding it as malformed.
    """
    match = ISOFORM_RE.match(upper(value))
    if not match:
        return None
    parent = match.group(1)
    if not looks_like_accession(parent):
        return None
    return (parent, match.group(2))


def normalize_organism(value):
    """Canonical comparison forms for one organism string.

    Returns a set, because a source may name an organism scientifically, by common name, or with
    an abbreviated genus, and any of those should compare equal to the authority's answer.
    """
    text = squash(value)
    if not text:
        return set()
    forms = set()
    bare = strip_parenthetical(text)
    for candidate in (text, bare):
        candidate = slug(candidate)
        if candidate:
            forms.add(candidate)
    # Pull the parenthetical out too: "Homo sapiens (Human)" also asserts the common name.
    for inner in re.findall(r"\(([^)]*)\)", text):
        if slug(inner):
            forms.add(slug(inner))
    return forms


def expand_abbreviated_genus(value):
    """``H. sapiens`` -> ``('h', 'sapiens')``, else ``None``.

    An abbreviated genus cannot be compared literally, only structurally: initial letter plus
    species epithet.
    """
    match = re.match(r"^\s*([A-Za-z])\.\s*([A-Za-z][A-Za-z\-]+)\s*$", strip_parenthetical(value or ""))
    if not match:
        return None
    return (match.group(1).lower(), match.group(2).lower())


def organism_matches(claimed, scientific_name, common_names=(), tax_id=None, claimed_tax_id=None):
    """Does a row's organism claim agree with what the authority returned?

    Agreement is deliberately generous about *spelling* and strict about *identity*.
    """
    if claimed_tax_id and tax_id and str(claimed_tax_id).strip() == str(tax_id).strip():
        # An explicit, matching NCBI taxon id settles it regardless of how the name is spelled.
        return True

    claimed_forms = normalize_organism(claimed)
    if not claimed_forms:
        return True  # No claim made, so nothing to contradict.

    authority_forms = set()
    authority_forms |= normalize_organism(scientific_name)
    for name in common_names or ():
        authority_forms |= normalize_organism(name)
    if claimed_forms & authority_forms:
        return True

    abbreviated = expand_abbreviated_genus(claimed)
    if abbreviated and scientific_name:
        parts = slug(scientific_name).split()
        if len(parts) >= 2 and parts[0][:1] == abbreviated[0] and parts[1] == abbreviated[1]:
            return True
    return False


def names_agree(left, right):
    """Loose protein-name equality: casing, hyphens and punctuation are not defects."""
    left_slug, right_slug = slug(left), slug(right)
    if not left_slug or not right_slug:
        return False
    if left_slug == right_slug:
        return True
    return left_slug in right_slug or right_slug in left_slug


def name_similarity(text, candidates):
    """Fraction of a description's informative tokens covered by any candidate name.

    Used only to *rank* candidates that the authority already put forward — never to invent one.
    """
    text_tokens = set(tokens(text))
    if not text_tokens:
        return 0.0
    best = 0.0
    for candidate in candidates:
        candidate_tokens = set(tokens(candidate))
        if not candidate_tokens:
            continue
        overlap = len(text_tokens & candidate_tokens) / float(len(candidate_tokens))
        best = max(best, overlap)
    return best
