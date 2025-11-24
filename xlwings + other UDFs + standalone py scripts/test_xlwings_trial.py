# D:\Dev\test_xlwings_trial.py
import xlwings as xw
import pandas as pd
import polars as pl
from typing import Any, List
import re

# ---------- helper: safe whole-word-ish matcher can be embedded in Polars expression ----------
STATES_AND_CODES = [
    # full names
    "alabama","alaska","arizona","arkansas","california","colorado","connecticut","delaware",
    "florida","georgia","hawaii","idaho","illinois","indiana","iowa","kansas","kentucky",
    "louisiana","maine","maryland","massachusetts","michigan","minnesota","mississippi",
    "missouri","montana","nebraska","nevada","new hampshire","new jersey","new mexico",
    "new york","north carolina","north dakota","ohio","oklahoma","oregon","pennsylvania",
    "rhode island","south carolina","south dakota","tennessee","texas","utah","vermont",
    "virginia","washington","west virginia","wisconsin","wyoming",
    # codes
    "al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id","il","in","ia","ks","ky",
    "la","me","md","ma","mi","mn","ms","mo","mt","ne","nv","nh","nj","nm","ny","nc","nd",
    "oh","ok","or","pa","ri","sc","sd","tn","tx","ut","vt","va","wa","wv","wi","wy"
]

# Precompile a regex pattern for word-boundary matching (case-insensitive)
_pattern = re.compile(r"\b(" + "|".join(re.escape(s) for s in STATES_AND_CODES) + r")\b", flags=re.IGNORECASE)

def _normalize_to_text(val):
    """
    Helper to convert a single cell value to a safe text value:
      - if it's None -> return None
      - if it's a list -> join items with space
      - otherwise -> str(value).strip()
    """
    if val is None:
        return None
    try:
        # If it's a sequence (list/tuple), join items
        if isinstance(val, (list, tuple)):
            # convert elements to str and join with space
            return " ".join("" if v is None else str(v) for v in val).strip()
        else:
            s = str(val).strip()
            return s
    except Exception:
        return str(val)

def _filter_by_states_pl(df_pl: pl.DataFrame) -> pl.DataFrame:
    """Return subset of df_pl where Firm / Headquarters contains any state (whole-word aware)"""
    pat = _pattern.pattern
    return df_pl.filter(pl.col("Firm / Headquarters").str.to_lowercase().str.contains(pat, literal=False))

def _safe_split_firm_hq(df_pl: pl.DataFrame) -> pl.DataFrame:
    """
    Normalize 'Firm / Headquarters' (convert any list values to single text),
    then split into 'Firm' and 'Headquarters' safely.
    """
    colname = "Firm / Headquarters"

    if colname not in df_pl.columns:
        return df_pl

    # Step 1: Normalize the column to plain text (convert list -> joined string)
    # Use map_elements instead of apply (correct Polars method)
    df_pl = df_pl.with_columns([
        pl.col(colname)
          .map_elements(lambda v: _normalize_to_text(v), return_dtype=pl.Utf8)
          .alias(colname)
    ])

    # Step 2: split into parts (array) then extract 0 & 1
    parts = pl.col(colname).str.split("/")  # returns array expression
    df_pl = df_pl.with_columns([
        parts.list.get(0).alias("Firm"),
        parts.list.get(1).alias("Headquarters")
    ])

    # Step 3: Trim whitespace using regex replace (portable)
    df_pl = df_pl.with_columns([
        pl.col("Firm").str.replace_all(r"^\s+|\s+$", "").alias("Firm"),
        pl.col("Headquarters").str.replace_all(r"^\s+|\s+$", "").alias("Headquarters")
    ])

    return df_pl


@xw.func  # this exposes the function as an Excel UDF
@xw.ret(index=False)
def PROCESS_TABLE(data: Any) -> pd.DataFrame:
    """
    UDF callable from Excel:
    =PROCESS_TABLE(A1:C1000)

    - 'data' will be an array-like (first row = headers)
    - returns a table (pandas DataFrame) which Excel will spill into cells
    Notes:
      * Keep the input range to a reasonable size when testing (Excel -> Python transfer is costly),
      * For very large datasets prefer the RunPython 'button' approach that writes to a sheet.
    """
    # Guard: if called with an Excel Range it will be passed as a list of lists
    if data is None:
        return pd.DataFrame([["No data"]])

    # If xlwings passes a pandas.DataFrame directly (some modes), handle that
    if isinstance(data, pd.DataFrame):
        pdf = data.copy()
    else:
        # data is likely a list of lists where first row contains headers
        try:
            rows = list(data)
        except Exception:
            # can't iterate – just return empty frame
            return pd.DataFrame([["Invalid input"]])

        if len(rows) < 1:
            return pd.DataFrame([["No rows"]])

        headers = rows[0]
        body = rows[1:] if len(rows) > 1 else []
        pdf = pd.DataFrame(body, columns=headers)

    # Convert to Polars
    try:
        df = pl.from_pandas(pdf)
    except Exception:
        # fallback: build DataFrame manually (less likely)
        pdf = pd.DataFrame(rows[1:], columns=rows[0])
        df = pl.from_pandas(pdf)

    # Ensure target columns exist
    if "Firm / Headquarters" not in df.columns:
        return pd.DataFrame([["Missing column: Firm / Headquarters"]])

    # Filter by states (whole-word using regex)
    try:
        df_filtered = _filter_by_states_pl(df)
    except Exception:
        # fallback to naive lowercase contains OR
        patterns = "|".join(re.escape(s) for s in STATES_AND_CODES)
        df_filtered = df.filter(pl.col("Firm / Headquarters").str.to_lowercase().str.contains(patterns))

    # Safe split to Firm / Headquarters
    df_filtered = _safe_split_firm_hq(df_filtered)

    # Trim MP / CEO and convert Rank to string if present
    if "MP / CEO" in df_filtered.columns:
        df_filtered = df_filtered.with_columns(pl.col("MP / CEO").str.strip_chars().alias("MP / CEO"))
    if "Rank" in df_filtered.columns:
        # Convert Rank to string first (it might be numeric), then strip
        df_filtered = df_filtered.with_columns(
            pl.col("Rank").cast(pl.Utf8).str.strip_chars().alias("Rank")
        )

    # Group by Firm + Headquarters and aggregate MP / CEO only
    agg_df = (
        df_filtered
        .group_by(["Firm", "Headquarters"], maintain_order=True)
        .agg([
            pl.count().alias("Count"),
            # Collect unique MP / CEO values and join with '; '
            pl.col("MP / CEO").drop_nulls().unique().str.concat("; ").alias("MP_CEO")
        ])
        .sort("Firm")
    )

    # Convert back to pandas for Excel output
    out_pdf = agg_df.to_pandas()
    # Reorder columns - Firm, Headquarters, MP_CEO, Count
    cols = ["Firm", "Headquarters", "MP_CEO", "Count"]
    out_pdf = out_pdf[cols]

    return out_pdf
