#!/usr/bin/env python3
"""
Validate {name}_papers_classified.jsonl before generating final output.
Usage: python validate_papers.py <path_to_classified_jsonl>

In the simplified workflow, classified JSONL should ONLY contain:
  A-class: first/second author AND top venue
  B-class: global top 5 by citations (any position, any venue)
All other papers must be discarded during Step 2.
"""

import json
import sys
from pathlib import Path


def validate_classified_papers(filepath: str) -> dict:
    """Validate classified papers JSONL and return stats + errors."""
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    errors = []
    warnings = []
    papers = []

    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                paper = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {i}: Invalid JSON: {e}")
                continue

            papers.append(paper)

            title = paper.get("title", "<missing title>")

            # Required fields
            required = [
                "title", "authors", "target_author_position",
                "target_author_index", "venue", "year", "citations",
                "is_top_venue", "domain", "label", "include_in_table"
            ]
            for field in required:
                if field not in paper:
                    errors.append(f"Line {i} ({title}): Missing required field '{field}'")

            # target_author_position consistency
            pos = paper.get("target_author_position")
            idx = paper.get("target_author_index")
            authors = paper.get("authors", [])

            if pos not in ("first", "second", "other"):
                errors.append(f"Line {i} ({title}): Invalid target_author_position '{pos}'")

            if isinstance(idx, int) and isinstance(authors, list):
                if idx >= len(authors):
                    errors.append(
                        f"Line {i} ({title}): target_author_index ({idx}) >= authors length ({len(authors)})"
                    )
                expected_pos = "first" if idx == 0 else "second" if idx == 1 else "other"
                if pos != expected_pos:
                    errors.append(
                        f"Line {i} ({title}): target_author_position '{pos}' does not match "
                        f"target_author_index {idx} (expected '{expected_pos}')"
                    )

            # Co-first author check: if author's name contains '*', position must be 'first'
            if isinstance(authors, list) and isinstance(idx, int) and idx < len(authors):
                author_name = authors[idx]
                if "*" in str(author_name) and pos != "first":
                    errors.append(
                        f"Line {i} ({title}): Author '{author_name}' contains '*' but "
                        f"target_author_position is '{pos}' (must be 'first')"
                    )

            # is_top_venue consistency
            is_top = paper.get("is_top_venue")
            venue = paper.get("venue", "")
            if is_top is True and not venue:
                warnings.append(
                    f"Line {i} ({title}): is_top_venue is True but venue is empty"
                )

    if not papers:
        errors.append("No papers found in the file")
        return {"ok": False, "errors": errors, "warnings": warnings}

    # Determine global top-5 by citations across ALL papers on the profile
    # (Note: the classified JSONL only contains a subset, but the top-5 check
    #  is still valid for the papers that made it into the file)
    sorted_by_citations = sorted(papers, key=lambda p: p.get("citations", 0), reverse=True)
    top5_titles = {p.get("title") for p in sorted_by_citations[:5]}

    # Validate that EVERY paper in classified JSONL is either A-class or B-class
    for paper in papers:
        title = paper.get("title", "<missing title>")
        pos = paper.get("target_author_position")
        is_top = paper.get("is_top_venue")
        include = paper.get("include_in_table")

        is_a_class = pos in ("first", "second") and is_top is True
        is_b_class = title in top5_titles

        if not is_a_class and not is_b_class:
            errors.append(
                f"({title}): Paper is neither A-class (first/second + top venue) "
                f"nor B-class (global top 5). It should have been discarded in Step 2. "
                f"(position={pos}, is_top_venue={is_top}, citations={paper.get('citations')})"
            )

        if include is not True:
            errors.append(
                f"({title}): include_in_table is {include}, but all papers in "
                f"classified JSONL must have include_in_table=True"
            )

    # Compute summary stats (only A-class first/second authors count toward citation stats)
    a_class_papers = [
        p for p in papers
        if p.get("target_author_position") in ("first", "second") and p.get("is_top_venue") is True
    ]

    first_top_citations = sum(
        p["citations"] for p in a_class_papers
        if p.get("target_author_position") == "first"
    )
    second_top_citations = sum(
        p["citations"] for p in a_class_papers
        if p.get("target_author_position") == "second"
    )
    total_top_citations = first_top_citations + second_top_citations

    b_class_papers = [p for p in papers if p.get("title") in top5_titles]

    print(f"=== Validation Results for {filepath} ===")
    print(f"Total papers in classified JSONL: {len(papers)}")
    print(f"  A-class (first/second + top venue): {len(a_class_papers)}")
    print(f"  B-class (global top 5): {len(b_class_papers)}")
    print()
    print(f"First-author top-venue citations: {first_top_citations}")
    print(f"Second-author top-venue citations: {second_top_citations}")
    print(f"Total first/second top-venue citations: {total_top_citations}")
    print()

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if not errors and not warnings:
        print("All validations passed.")
    elif not errors:
        print("No errors (warnings only).")
    else:
        print("Validation failed. Please fix errors before generating output.")

    return {
        "total_papers": len(papers),
        "a_class": len(a_class_papers),
        "b_class": len(b_class_papers),
        "first_top_citations": first_top_citations,
        "second_top_citations": second_top_citations,
        "total_top_citations": total_top_citations,
        "errors": errors,
        "warnings": warnings,
        "ok": len(errors) == 0,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_papers.py <path_to_classified_jsonl>")
        sys.exit(1)

    result = validate_classified_papers(sys.argv[1])
    sys.exit(0 if result["ok"] else 1)
