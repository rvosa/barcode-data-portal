"""
Extract BOLDetective ranks from BCDM JSON-L records.

This script evaluates each BCDM record against the 16 BOLDetective criteria
and assigns a quality rank (1-7) based on hierarchical criteria satisfaction.

Usage:
    cat BCDM.jsonl | python extract_rank_summary.py --output_file ranks.jsonl

Output format (JSON-L):
    {"processid": "AACTA2950-20", "rank": 4, "sumscore": 11, "criteria": {...}}
"""

import sys
import ujson as json
import argparse
import re
import traceback
from typing import Dict, Any

# =============================================================================
# Pattern definitions for criteria evaluation
# =============================================================================

# Type specimen patterns (holotype, paratype, syntype, lectotype, neotype, type)
TYPE_PATTERNS = re.compile(
    r"\b(holotype|paratype|syntype|lectotype|neotype|allotype|isotype|"
    r"paralectotype|topotype|cotype)\b",
    re.IGNORECASE,
)

# Also check for generic "type" in voucher_type field specifically
TYPE_VOUCHER_PATTERN = re.compile(r"\btype\b", re.IGNORECASE)

# Invalid species name patterns (sp., aff., cf., numbers, None)
INVALID_SPECIES_PATTERNS = re.compile(
    r"(?:^|\s)(sp\.|sp\s|spp\.|aff\.|cf\.|none)(?:\s|$)|\d+", re.IGNORECASE
)

# Automated identifier patterns (should NOT be considered named identifiers)
AUTOMATED_ID_PATTERNS = re.compile(
    r"\b(BOLD|BLAST|BIN|ID\s*Engine|Taxonomy\s*Match|Tree-Based)\b", re.IGNORECASE
)

# Morphological identification method patterns (positive indicators)
MORPHO_ID_PATTERNS = re.compile(
    r"\b(morpholog|dissect|genital|key|expert|visual|wing|habitus|male|female)\b",
    re.IGNORECASE,
)

# Molecular identification method patterns (negative if sole method)
MOLECULAR_ID_PATTERNS = re.compile(
    r"\b(barcode|BOLD|DNA|sequenc|phylogen|BLAST|BIN|molecular|genetic)\b",
    re.IGNORECASE,
)

# Private institution patterns (should fail institution_public criterion)
PRIVATE_INST_PATTERNS = re.compile(
    r"\b(personal|private|no\s*voucher|unvouchered|unknown)\b", re.IGNORECASE
)

# Voucher positive indicators (override negative)
VOUCHER_POSITIVE_PATTERNS = re.compile(
    r"\b(museum|herbarium|registered|type|national|university|institute|"
    r"collection|academy|zoo|aquarium)\b",
    re.IGNORECASE,
)

# Voucher negative indicators
VOUCHER_NEGATIVE_PATTERNS = re.compile(
    r"\b(DNA\s*only|e-vouch|private|no\s*voucher|unvouchered|destroyed|"
    r"lost|missing|discarded|released|consumed)\b",
    re.IGNORECASE,
)


# =============================================================================
# Criteria evaluation functions
# =============================================================================


def evaluate_species_level_id(record: Dict[str, Any]) -> int:
    """
    Criterion 1: Species-level identification.

    Pass if:
    - species field is populated
    - identification_rank is 'species' (or subspecies)
    - species name does not contain "sp.", "aff.", "cf.", numbers, or "None"
    """
    species = record.get("species", "")
    id_rank = record.get("identification_rank", "")

    if not species:
        return 0

    if id_rank not in ("species", "subspecies"):
        return 0

    if INVALID_SPECIES_PATTERNS.search(species):
        return 0

    return 1


def evaluate_bin_assigned(record: Dict[str, Any]) -> int:
    """
    Criterion 2: BIN assignment present.
    """
    bin_uri = record.get("bin_uri", "")
    return 1 if bin_uri else 0


def evaluate_sequence_quality(record: Dict[str, Any]) -> int:
    """
    Criterion 3: Sequence quality - minimum 500bp unambiguous nucleotides.

    Uses nuc_basecount if available, otherwise counts ACGT in nuc field.
    """
    # Prefer pre-calculated basecount
    basecount = record.get("nuc_basecount")
    if basecount is not None:
        return 1 if basecount >= 500 else 0

    # Fallback: count ACGT characters in sequence
    nuc = record.get("nuc", "")
    if nuc:
        acgt_count = sum(1 for c in nuc.upper() if c in "ACGT")
        return 1 if acgt_count >= 500 else 0

    return 0


def evaluate_type_status(record: Dict[str, Any]) -> int:
    """
    Criterion 4: Type specimen status.

    Check taxonomy_notes, collection_notes, and voucher_type fields for
    type designations (holotype, paratype, etc.).
    """
    # Check taxonomy_notes and collection_notes for specific type designations
    notes_text = " ".join(
        [
            str(record.get("taxonomy_notes", "")),
            str(record.get("collection_notes", "")),
        ]
    )
    if TYPE_PATTERNS.search(notes_text):
        return 1

    # Check voucher_type for "type" or specific type designations
    voucher_type = str(record.get("voucher_type", ""))
    if TYPE_PATTERNS.search(voucher_type):
        return 1

    # Also accept if voucher_type contains "type" as standalone word
    if TYPE_VOUCHER_PATTERN.search(voucher_type):
        # But exclude "voucher type" or "tissue type" etc.
        if not re.search(r"(voucher|tissue|sample|dna)\s*type", voucher_type, re.I):
            return 1

    return 0


def evaluate_identifier_named(record: Dict[str, Any]) -> int:
    """
    Criterion 6: Named identifier present.

    Pass if identified_by is populated and does NOT indicate automated methods
    (BOLD, BLAST, BIN, ID Engine, etc.).
    """
    identifier = record.get("identified_by", "")

    if not identifier:
        return 0

    # Fail if identifier indicates automated method
    if AUTOMATED_ID_PATTERNS.search(identifier):
        return 0

    return 1


def evaluate_id_method_morphological(record: Dict[str, Any]) -> int:
    """
    Criterion 7: Identification method is morphological.

    Pass if identification_method indicates morphological methods.
    Fail if purely molecular methods or if method is missing.
    Mixed methods (morpho + molecular) should pass.
    """
    id_method = record.get("identification_method", "")

    if not id_method:
        return 0

    has_morpho = bool(MORPHO_ID_PATTERNS.search(id_method))
    has_molecular = bool(MOLECULAR_ID_PATTERNS.search(id_method))

    # Pass if morphological indicators present
    if has_morpho:
        return 1

    # Fail if only molecular or no recognizable method
    return 0


def evaluate_country_present(record: Dict[str, Any]) -> int:
    """
    Criterion 8: Country/ocean present.
    """
    country = record.get("country/ocean", "")
    return 1 if country else 0


def evaluate_coords_present(record: Dict[str, Any]) -> int:
    """
    Criterion 9: GPS coordinates present.

    Must be a valid coordinate pair (list/tuple of 2 numbers).
    """
    coord = record.get("coord")

    if coord is None:
        return 0

    # Check it's a valid coordinate pair
    if isinstance(coord, (list, tuple)) and len(coord) == 2:
        try:
            lat, lon = coord
            # Basic validation: lat in [-90, 90], lon in [-180, 180]
            if (
                    isinstance(lat, (int, float))
                    and isinstance(lon, (int, float))
                    and -90 <= lat <= 90
                    and -180 <= lon <= 180
            ):
                return 1
        except (TypeError, ValueError):
            pass

    return 0


def evaluate_collection_date_present(record: Dict[str, Any]) -> int:
    """
    Criterion 10: Collection date present.

    Pass if either collection_date_start or collection_date_end is populated.
    """
    date_start = record.get("collection_date_start", "")
    date_end = record.get("collection_date_end", "")

    return 1 if (date_start or date_end) else 0


def evaluate_collector_present(record: Dict[str, Any]) -> int:
    """
    Criterion 11: Collector information present.
    """
    collectors = record.get("collectors", "")
    return 1 if collectors else 0


def evaluate_locality_present(record: Dict[str, Any]) -> int:
    """
    Criterion 12: Collection locality present.

    Pass if at least one of: region (state/province), sector, or site is populated.
    """
    # Note: BCDM uses "region" for state/province level
    region = record.get("region", "") or record.get("province/state", "")
    sector = record.get("sector", "")
    site = record.get("site", "")

    return 1 if (region or sector or site) else 0


def evaluate_institution_public(record: Dict[str, Any]) -> int:
    """
    Criterion 13: Public institution designation.

    Pass if inst field is populated and does NOT indicate private collection.
    """
    inst = record.get("inst", "")

    if not inst:
        return 0

    # Fail if indicates private/personal collection
    if PRIVATE_INST_PATTERNS.search(inst):
        return 0

    return 1


def evaluate_museum_id_present(record: Dict[str, Any]) -> int:
    """
    Criterion 14: Museum ID present.
    """
    museum_id = record.get("museumid", "")
    return 1 if museum_id else 0


def evaluate_voucher_status(record: Dict[str, Any]) -> int:
    """
    Criterion 15: Voucher status - positive indicators.

    Positive indicators (museum, herbarium, registered, type, national)
    override negative indicators (DNA only, e-vouch, private, destroyed, etc.).
    """
    voucher_type = record.get("voucher_type", "")

    if not voucher_type:
        return 0

    has_positive = bool(VOUCHER_POSITIVE_PATTERNS.search(voucher_type))
    has_negative = bool(VOUCHER_NEGATIVE_PATTERNS.search(voucher_type))

    # Positive overrides negative
    if has_positive:
        return 1

    # Fail if negative indicators present
    if has_negative:
        return 0

    # If neither positive nor negative, consider it a pass (voucher exists)
    return 1


def evaluate_criteria(record: Dict[str, Any]) -> Dict[str, int]:
    """
    Evaluate all 16 BOLDetective criteria for a single record.

    Returns dict with criterion name -> pass/fail (1/0).
    Note: has_image is always 0 (skipped - no image manifest available).
    """
    return {
        "species_level_id": evaluate_species_level_id(record),
        "bin_assigned": evaluate_bin_assigned(record),
        "sequence_quality": evaluate_sequence_quality(record),
        "type_status": evaluate_type_status(record),
        "has_image": 0,  # Skipped - no image manifest
        "identifier_named": evaluate_identifier_named(record),
        "id_method_morphological": evaluate_id_method_morphological(record),
        "country_present": evaluate_country_present(record),
        "coords_present": evaluate_coords_present(record),
        "collection_date_present": evaluate_collection_date_present(record),
        "collector_present": evaluate_collector_present(record),
        "locality_present": evaluate_locality_present(record),
        "institution_public": evaluate_institution_public(record),
        "museum_id_present": evaluate_museum_id_present(record),
        "voucher_status": evaluate_voucher_status(record),
    }


# =============================================================================
# Rank calculation
# =============================================================================


def calculate_rank(criteria: Dict[str, int]) -> int:
    """
    Calculate BOLDetective rank based on criteria satisfaction.

    Ranks are hierarchical (1 = best, 7 = worst):
    - Rank 7: No species-level ID
    - Rank 6: Species ID + BIN + sequence quality (minimum acceptable)
    - Rank 5: Rank 6 + country + coords + collection date
    - Rank 4: Rank 5 + identifier + ID method + image (image skipped)
    - Rank 3: Rank 4 + collector + locality
    - Rank 2: Rank 3 + public institution + museum ID + voucher status
    - Rank 1: Rank 2 + type specimen status

    Note: Since has_image is always 0 (skipped), Rank 4 requirements are
    adjusted to only require identifier_named and id_method_morphological.
    """
    # Rank 7: No species-level ID
    if not criteria["species_level_id"]:
        return 7

    # Rank 6 requirements (minimum acceptable for species-level data)
    rank6_met = criteria["bin_assigned"] and criteria["sequence_quality"]

    if not rank6_met:
        return 7  # Has species ID but doesn't meet minimum sequence requirements

    # Rank 5 requirements: geographic and temporal metadata
    rank5_met = rank6_met and (
            criteria["country_present"]
            and criteria["coords_present"]
            and criteria["collection_date_present"]
    )

    if not rank5_met:
        return 6

    # Rank 4 requirements: identification evidence
    # Note: has_image is skipped, so we only check identifier and ID method
    rank4_met = rank5_met and (
            criteria["identifier_named"] and criteria["id_method_morphological"]
        # and criteria["has_image"]  # Skipped
    )

    if not rank4_met:
        return 5

    # Rank 3 requirements: collector and locality
    rank3_met = rank4_met and (
            criteria["collector_present"] and criteria["locality_present"]
    )

    if not rank3_met:
        return 4

    # Rank 2 requirements: voucher repository information
    rank2_met = rank3_met and (
            criteria["institution_public"]
            and criteria["museum_id_present"]
            and criteria["voucher_status"]
    )

    if not rank2_met:
        return 3

    # Rank 1: Type specimen
    if criteria["type_status"]:
        return 1

    return 2


# =============================================================================
# Main processing
# =============================================================================


def main(args):
    """
    Process BCDM JSON-L records from stdin and output rank summaries.
    """
    records_processed = 0
    records_skipped = 0

    try:
        with open(args.output_file, "w") as out:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed JSON line: {e}", file=sys.stderr)
                    records_skipped += 1
                    continue

                processid = record.get("processid")

                if not processid:
                    records_skipped += 1
                    continue

                # Evaluate criteria
                criteria = evaluate_criteria(record)

                # Calculate rank and sumscore
                rank = calculate_rank(criteria)
                sumscore = sum(criteria.values())

                # Build output record
                result = {
                    "processid": processid,
                    "rank": rank,
                    "sumscore": sumscore,
                    "criteria": criteria,
                }

                out.write(json.dumps(result) + "\n")
                records_processed += 1

        # Summary to stderr
        print(
            f"Processed {records_processed} records, skipped {records_skipped}",
            file=sys.stderr,
        )

    except Exception as e:
        print(traceback.format_exc(), file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract BOLDetective ranks from BCDM JSON-L records",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    cat BCDM.jsonl | python extract_rank_summary.py --output_file ranks.jsonl

    zcat BCDM.jsonl.gz | python extract_rank_summary.py --output_file ranks.jsonl

Output format (JSON-L):
    {
        "processid": "AACTA2950-20",
        "rank": 4,
        "sumscore": 11,
        "criteria": {
            "species_level_id": 1,
            "bin_assigned": 1,
            "sequence_quality": 1,
            "type_status": 0,
            "has_image": 0,
            "identifier_named": 1,
            "id_method_morphological": 0,
            "country_present": 1,
            "coords_present": 1,
            "collection_date_present": 1,
            "collector_present": 1,
            "locality_present": 1,
            "institution_public": 1,
            "museum_id_present": 1,
            "voucher_status": 1
        }
    }

Rank definitions:
    Rank 1: Type specimens with full documentation
    Rank 2: Full documentation (institution, museum ID, voucher status)
    Rank 3: Good documentation (collector, locality)
    Rank 4: Verified identification (named identifier, morphological method)
    Rank 5: Basic metadata (country, coordinates, collection date)
    Rank 6: Minimum acceptable (species ID, BIN, sequence quality)
    Rank 7: Below minimum (no species-level ID or insufficient data)
        """,
    )
    parser.add_argument(
        "--output_file",
        type=str,
        required=True,
        help="Output JSON-L file path for rank summaries",
    )

    args = parser.parse_args()
    main(args)