"""Cleanup Microsoft-prefixed tech stack entries.

This script:
1. Finds programming languages and ecosystems whose names start with "Microsoft".
2. Determines canonical names by stripping Microsoft-specific prefixes.
3. Merges duplicates into existing canonical entries when possible.
4. Otherwise renames the entry and updates aliases to ensure future normalization.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from loguru import logger

from database.client import db


@dataclass
class TechItem:
    id: str
    name: str
    display_name: str
    type: str  # "language" or "ecosystem"
    relevance_score: Optional[int]


PREFIX_RULES: List[Tuple[str, str]] = [
    ("microsoft azure ", "Azure "),
    ("microsoft power ", "Power "),
    ("microsoft sql ", "SQL "),
    ("microsoft dynamics ", "Dynamics "),
    ("microsoft office ", "Office "),
    ("microsoft windows ", "Windows "),
]
DEFAULT_PREFIX = "microsoft "


def derive_canonical_name(name: str) -> Optional[str]:
    lower = name.lower()

    for prefix, replacement in PREFIX_RULES:
        if lower.startswith(prefix):
            remainder = name[len(prefix):]
            return f"{replacement}{remainder}".strip()

    if lower.startswith(DEFAULT_PREFIX):
        remainder = name[len(DEFAULT_PREFIX):]
        return remainder.strip()

    return None


def fetch_microsoft_items() -> List[TechItem]:
    items: List[TechItem] = []

    ecosystems = db.get_all_ecosystems(active_only=True) or []
    for eco in ecosystems:
        name = eco["name"]
        if name.lower().startswith("microsoft "):
            items.append(
                TechItem(
                    id=eco["id"],
                    name=name,
                    display_name=eco.get("display_name", name),
                    type="ecosystem",
                    relevance_score=eco.get("relevance_score"),
                )
            )

    languages = db.get_all_programming_languages(active_only=True) or []
    for lang in languages:
        name = lang["name"]
        if name.lower().startswith("microsoft "):
            items.append(
                TechItem(
                    id=lang["id"],
                    name=name,
                    display_name=lang.get("display_name", name),
                    type="language",
                    relevance_score=lang.get("relevance_score"),
                )
            )

    return items


def _table_for_type(tech_type: str) -> str:
    return "programming_languages" if tech_type == "language" else "ecosystems"


def find_existing_item(canonical_name: str, tech_type: str) -> Optional[Dict]:
    table = "programming_languages" if tech_type == "language" else "ecosystems"
    result = (
        db.client.table(table)
        .select("*")
        .eq("name", canonical_name)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    return result.data if result and result.data else None


def find_item_any_status(canonical_name: str, tech_type: str) -> Optional[Dict]:
    table = _table_for_type(tech_type)
    result = (
        db.client.table(table)
        .select("*")
        .eq("name", canonical_name)
        .maybe_single()
        .execute()
    )
    return result.data if result and result.data else None


def get_assignments(tech_id: str, tech_type: str) -> List[Dict]:
    table = "job_programming_languages" if tech_type == "language" else "job_ecosystems"
    column = "programming_language_id" if tech_type == "language" else "ecosystem_id"
    result = (
        db.client.table(table)
        .select("*")
        .eq(column, tech_id)
        .execute()
    )
    return result.data if result and result.data else []


def assignment_exists(job_id: str, canonical_id: str, tech_type: str) -> bool:
    table = "job_programming_languages" if tech_type == "language" else "job_ecosystems"
    column = "programming_language_id" if tech_type == "language" else "ecosystem_id"
    result = (
        db.client.table(table)
        .select("id")
        .eq("job_posting_id", job_id)
        .eq(column, canonical_id)
        .maybe_single()
        .execute()
    )
    return bool(result and result.data)


def update_assignment(assignment_id: str, canonical_id: str, tech_type: str) -> None:
    table = "job_programming_languages" if tech_type == "language" else "job_ecosystems"
    column = "programming_language_id" if tech_type == "language" else "ecosystem_id"
    db.client.table(table).update({column: canonical_id}).eq("id", assignment_id).execute()


def delete_assignment(assignment_id: str, tech_type: str) -> None:
    table = "job_programming_languages" if tech_type == "language" else "job_ecosystems"
    db.client.table(table).delete().eq("id", assignment_id).execute()


def deactivate_item(item: TechItem) -> None:
    table = "programming_languages" if item.type == "language" else "ecosystems"
    db.client.table(table).update({"is_active": False}).eq("id", item.id).execute()


def reactivate_item(item_id: str, tech_type: str) -> None:
    table = _table_for_type(tech_type)
    db.client.table(table).update({"is_active": True}).eq("id", item_id).execute()


def rename_item(item: TechItem, canonical_name: str) -> None:
    table = _table_for_type(item.type)
    db.client.table(table).update({"name": canonical_name, "display_name": canonical_name}).eq("id", item.id).execute()


def create_alias(alias: str, canonical_name: str, tech_type: str, notes: str) -> None:
    try:
        (
            db.client.table("tech_stack_aliases")
            .insert(
                {
                    "alias": alias,
                    "canonical_name": canonical_name,
                    "type": tech_type,
                    "notes": notes,
                }
            )
            .execute()
        )
    except Exception as exc:  # Duplicate insert is fine
        message = str(exc).lower()
        if "duplicate" not in message and "unique" not in message:
            logger.warning(f"Failed to create alias {alias} → {canonical_name}: {exc}")


def merge_into_canonical(item: TechItem, canonical: Dict) -> Tuple[int, int]:
    canonical_id = canonical["id"]
    assignments = get_assignments(item.id, item.type)
    updated = 0
    deleted = 0

    for assignment in assignments:
        job_id = assignment["job_posting_id"]
        if assignment_exists(job_id, canonical_id, item.type):
            delete_assignment(assignment["id"], item.type)
            deleted += 1
        else:
            update_assignment(assignment["id"], canonical_id, item.type)
            updated += 1

    deactivate_item(item)
    create_alias(item.name, canonical["name"], item.type, "Microsoft prefix cleanup")

    logger.info(
        f"    Merged {item.name} → {canonical['name']} (updated: {updated}, deleted: {deleted})"
    )
    return updated, deleted


def rename_to_canonical(item: TechItem, canonical_name: str) -> None:
    try:
        rename_item(item, canonical_name)
        create_alias(item.name, canonical_name, item.type, "Microsoft prefix rename")
        logger.info(f"    Renamed {item.name} → {canonical_name}")
    except Exception as exc:
        message = str(exc)
        if "23505" in message or "duplicate key" in message.lower():
            logger.warning(
                f"    Rename conflict for {item.name} → {canonical_name}. Falling back to merge"
            )
            existing = find_item_any_status(canonical_name, item.type)
            if existing:
                if not existing.get("is_active"):
                    reactivate_item(existing["id"], item.type)
                merge_into_canonical(item, existing)
            else:
                raise
        else:
            raise


def cleanup_microsoft_prefixes() -> None:
    items = fetch_microsoft_items()
    logger.info(f"Found {len(items)} Microsoft-prefixed tech items")

    if not items:
        logger.info("Nothing to clean up")
        return

    totals = defaultdict(int)

    for item in items:
        canonical_name = derive_canonical_name(item.name)
        if not canonical_name:
            logger.debug(f"Skipping {item.name} (no canonical derived)")
            continue

        if canonical_name == item.name:
            logger.debug(f"Skipping {item.name} (already canonical)")
            continue

        logger.info(f"Processing {item.name} ({item.type}) → {canonical_name}")

        existing = find_existing_item(canonical_name, item.type)
        if not existing:
            inactive_candidate = find_item_any_status(canonical_name, item.type)
            if inactive_candidate:
                logger.info(
                    f"    Reactivating inactive canonical entry {canonical_name} for merging"
                )
                reactivate_item(inactive_candidate["id"], item.type)
                inactive_candidate["is_active"] = True
                existing = inactive_candidate
        if existing:
            updated, deleted = merge_into_canonical(item, existing)
            totals["assignments_updated"] += updated
            totals["assignments_deleted"] += deleted
            totals["deactivated"] += 1
        else:
            rename_to_canonical(item, canonical_name)
            totals["renamed"] += 1

    logger.success(
        "Cleanup complete: "
        f"{totals['deactivated']} deactivated, "
        f"{totals['renamed']} renamed, "
        f"{totals['assignments_updated']} assignments updated, "
        f"{totals['assignments_deleted']} assignments deleted"
    )


if __name__ == "__main__":
    cleanup_microsoft_prefixes()
