# collector.py from https://github.com/sgofferj/tak-shadowfleet-id
#
# Copyright Stefan Gofferje
#
# Licensed under the Gnu General Public License Version 3 or higher (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.gnu.org/licenses/gpl-3.0.en.html

import argparse
import io
import json
import os
import re
import traceback
from datetime import datetime
from typing import Any, Dict, List, cast

import pandas as pd
import requests

# Configuration
DATASET_PATH = "shadowfleet.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
)

# OpenSanctions Simple CSV
OPENSANCTIONS_URL = (
    "https://data.opensanctions.org/datasets/latest/sanctions/targets.simple.csv"
)
UK_URL = "https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.csv"


def clean_val(val: Any, default: str = "Unknown") -> str:
    if pd.isna(val) or str(val).lower() in ["nan", "none", ""]:
        return default
    return str(val).strip()


def get_cot_type(vessel_type_str: str) -> str:
    v = str(vessel_type_str).lower()
    if any(k in v for k in ["tanker", "oil", "chemical"]):
        return "a-s-S-X-M-O"
    if any(k in v for k in ["lng", "lpg", "gas", "carrier"]):
        return "a-s-S-X-M-P"
    return "a-s-S-X-M"  # Default Cargo/Logistics


def fetch_data(url: str) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    # Increased timeout to 300 for reliability in CI
    response = requests.get(url, headers=headers, timeout=300)
    response.raise_for_status()
    return response.content


# pylint: disable=too-many-locals
def parse_opensanctions(csv_content: bytes) -> Dict[str, Dict[str, Any]]:
    try:
        df = pd.read_csv(io.BytesIO(csv_content), low_memory=False)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Failed to read OpenSanctions CSV: {e}")
        return {}

    df.columns = [c.strip() for c in df.columns]

    if "schema" not in df.columns:
        print("Error: 'schema' column missing in OpenSanctions CSV")
        return {}

    df_vessels = df[df["schema"].str.strip().isin(["Vessel", "vessel"])]

    if df_vessels.empty:
        print("No vessels found in OpenSanctions schema.")
        return {}

    vessels: Dict[str, Dict[str, Any]] = {}

    for _, row in df_vessels.iterrows():
        identifiers_str = str(row.get("identifiers", ""))
        identifiers = (
            identifiers_str.split(";") if identifiers_str not in ("nan", "") else []
        )

        imo = None
        mmsi_list = []
        for ident in identifiers:
            ident = ident.strip().upper()
            imo_match = re.search(r"IMO\s*(\d{7})", ident)
            if imo_match:
                imo = imo_match.group(1)
            elif re.fullmatch(r"\d{9}", ident):
                mmsi_list.append(ident)

        if not imo:
            continue

        names = []
        primary_name = clean_val(row.get("name"), "None")
        if primary_name != "None":
            names.append(primary_name)

        aliases_str = str(row.get("aliases", ""))
        aliases = aliases_str.split(";") if aliases_str not in ("nan", "") else []
        for alias in aliases:
            alias = alias.strip()
            if alias and alias.lower() != "nan" and alias not in names:
                names.append(alias)

        flag = clean_val(row.get("countries")).replace(";", ", ")
        if flag.lower() == "nan":
            flag = "Unknown"

        cot = get_cot_type(primary_name if primary_name != "None" else "Vessel")

        vessels[imo] = {
            "imo": imo,
            "mmsi": list(set(mmsi_list)),
            "names": names,
            "type": "Vessel",
            "operator": "Unknown",
            "flag": flag,
            "cot": cot,
            "sanctions_origin": ["OpenSanctions"],
            "last_updated": datetime.now().isoformat(),
        }
    return vessels


# pylint: disable=too-many-locals
def parse_uk(csv_content: bytes) -> Dict[str, Dict[str, Any]]:
    try:
        lines = csv_content.decode("utf-8", errors="replace").splitlines()
        if lines and lines[0].startswith("Report Date:"):
            csv_data = "\n".join(lines[1:])
        else:
            csv_data = "\n".join(lines)

        df = pd.read_csv(io.StringIO(csv_data), low_memory=False)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Failed to read UK CSV: {e}")
        return {}

    df.columns = [c.strip() for c in df.columns]

    vessels: Dict[str, Dict[str, Any]] = {}
    filter_cols = ["Designation Type", "Type of entity"]
    df_ships = pd.DataFrame()
    for col in filter_cols:
        if col in df.columns:
            temp_ships = df[df[col].str.contains("Ship", case=False, na=False)]
            df_ships = pd.concat([df_ships, temp_ships]).drop_duplicates()

    if df_ships.empty and "IMO number" in df.columns:
        df_ships = df[df["IMO number"].notna()]

    for _, row in df_ships.iterrows():
        imo_val = row.get("IMO number")
        if pd.isna(imo_val):
            continue

        imo = re.sub(r"\D", "", str(imo_val))
        if not imo:
            continue

        name = clean_val(row.get("Name 6"))
        vtype = clean_val(row.get("Type of ship"))
        flag = clean_val(row.get("Current believed flag of ship"))
        operator = clean_val(row.get("Current owner/operator (s)"))

        vessels[imo] = {
            "imo": imo,
            "mmsi": [],
            "names": [name] if name != "Unknown" else [],
            "type": vtype,
            "operator": operator,
            "flag": flag,
            "cot": get_cot_type(vtype if vtype != "Unknown" else name),
            "sanctions_origin": ["UK"],
            "last_updated": datetime.now().isoformat(),
        }
    return vessels


def merge_datasets(
    existing: Dict[str, Dict[str, Any]], new_data: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    for imo, data in new_data.items():
        if imo in existing:
            existing[imo]["mmsi"] = list(
                set(existing[imo].get("mmsi", []) + data.get("mmsi", []))
            )
            existing[imo]["names"] = list(
                set(existing[imo].get("names", []) + data.get("names", []))
            )
            origins = cast(List[str], existing[imo].get("sanctions_origin", []))
            for o in data.get("sanctions_origin", []):
                if o not in origins:
                    origins.append(o)
            existing[imo]["sanctions_origin"] = origins
            existing[imo]["last_updated"] = datetime.now().isoformat()

            # Update fields if they were unknown/empty but are now known
            if (existing[imo].get("flag") in ["Unknown", "nan", ""]) and data.get(
                "flag"
            ) not in ["Unknown", "nan", ""]:
                existing[imo]["flag"] = data["flag"]
            if (
                existing[imo].get("type") in ["Vessel", "Unknown", "nan", ""]
            ) and data.get("type") not in ["Vessel", "Unknown", "nan", ""]:
                existing[imo]["type"] = data["type"]
            if (existing[imo].get("operator") in ["Unknown", "nan", ""]) and data.get(
                "operator"
            ) not in ["Unknown", "nan", ""]:
                existing[imo]["operator"] = data["operator"]
        else:
            existing[imo] = data
    return existing


def main() -> None:
    parser = argparse.ArgumentParser(description="Shadow Fleet Sanctions Collector")
    parser.parse_args()

    dataset: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(DATASET_PATH):
        try:
            with open(DATASET_PATH, "r", encoding="utf-8") as f:
                dataset_list = json.load(f)
                dataset = {v["imo"]: v for v in dataset_list if "imo" in v}
        except Exception:  # pylint: disable=broad-exception-caught
            dataset = {}

    print("Fetching OpenSanctions data...")
    try:
        os_csv = fetch_data(OPENSANCTIONS_URL)
        os_vessels = parse_opensanctions(os_csv)
        dataset = merge_datasets(dataset, os_vessels)
        print(f"Processed {len(os_vessels)} vessels from OpenSanctions.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error processing OpenSanctions: {e}")
        traceback.print_exc()

    print("Fetching UK data...")
    try:
        uk_csv = fetch_data(UK_URL)
        uk_vessels = parse_uk(uk_csv)
        dataset = merge_datasets(dataset, uk_vessels)
        print(f"Processed {len(uk_vessels)} vessels from UK.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error processing UK: {e}")
        traceback.print_exc()

    # Convert back to list
    final_list = list(dataset.values())

    try:
        with open(DATASET_PATH, "w", encoding="utf-8") as f:
            json.dump(final_list, f, indent=2)
        print(f"Saved {len(final_list)} unique vessels to {DATASET_PATH}.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error saving dataset: {e}")


if __name__ == "__main__":
    main()
