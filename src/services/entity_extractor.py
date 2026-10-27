import re
from src.models.domain import validate_canonical_urn

EXPLICIT_URN_REGEX = re.compile(
    r"\burn:(?:system|resource|role|actor|step|doc|chunk):[a-zA-Z0-9_\-:.]+"
)

# Maps natural language domain phrases in policies to canonical graph URNs
DEFAULT_ALIAS_MAP: dict[str, list[str]] = {
    "invoice tables": ["urn:resource:billing_db:table:invoices"],
    "invoice records": ["urn:resource:billing_db:table:invoices"],
    "invoices": ["urn:resource:billing_db:table:invoices"],
    "billing database": ["urn:system:billing_db"],
    "billing_db": ["urn:system:billing_db"],
    "finance_operator": ["urn:role:finance_operator"],
    "interns": ["urn:role:intern", "urn:actor:intern_bob"],
    "intern": ["urn:role:intern", "urn:actor:intern_bob"],
}


def extract_referenced_urns(
    text: str,
    custom_aliases: dict[str, list[str]] | None = None,
) -> list[str]:
    discovered: list[str] = []
    seen: set[str] = set()

    for match in EXPLICIT_URN_REGEX.finditer(text):
        candidate = match.group(0).rstrip(".,:;!?)]\"'`")
        try:
            validated = validate_canonical_urn(candidate)
            if validated not in seen:
                seen.add(validated)
                discovered.append(validated)
        except ValueError:
            continue

    alias_map = dict(DEFAULT_ALIAS_MAP)
    if custom_aliases:
        for key, val in custom_aliases.items():
            alias_map[key.lower()] = val

    lowered_text = text.lower()
    for phrase, mapped_urns in alias_map.items():
        if re.search(rf"\b{re.escape(phrase.lower())}\b", lowered_text):
            for urn in mapped_urns:
                try:
                    validated = validate_canonical_urn(urn)
                    if validated not in seen:
                        seen.add(validated)
                        discovered.append(validated)
                except ValueError:
                    continue

    return discovered
