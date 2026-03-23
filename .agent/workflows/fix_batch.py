"""
fix_batch.py — Apply enrichment data to ticker reports.

Usage:
  1. Populate the DATA dict below with ticker enrichment data
  2. Run: python .agent/workflows/fix_batch.py
  3. IMPORTANT: Clear DATA dict after each batch to prevent regressions

DATA dict format:
  "XXXX": {
      "desc": "Traditional Chinese description with [[wikilinks]]...",
      "supply_chain": "**上游:**\\n- ...\\n**中游:**\\n- ...\\n**下游:**\\n- ...",
      "cust": "### 主要客戶\\n- ...\\n\\n### 主要供應商\\n- ...",
  }
"""

import os, glob, sys, re

# =============================================================================
# DATA DICT — Populate for current batch, clear after each run
# =============================================================================
DATA = {
    # Example (delete before use):
    # "XXXX": {
    #     "desc": "公司描述 with [[wikilinks]]",
    #     "supply_chain": "**上游:**\n- ...\n\n**中游:**\n- ...\n\n**下游:**\n- ...",
    #     "cust": "### 主要客戶\n- ...\n\n### 主要供應商\n- ...",
    # },
}

# =============================================================================
# METADATA FIXES — Add metadata to files missing 板塊/產業/市值/企業價值
# =============================================================================
METADATA_FIXES = {
    # "XXXX": {"sector": "Technology", "industry": "Semiconductors"},
}

# =============================================================================
# Engine — do not edit below unless changing enrichment logic
# =============================================================================
BASE_DIR = r"F:\My TW Coverage\Pilot_Reports"


def update_file(filepath, ticker):
    if ticker not in DATA:
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    new_data = DATA[ticker]

    # Add metadata if missing and specified in METADATA_FIXES
    if ticker in METADATA_FIXES:
        meta = METADATA_FIXES[ticker]
        if "**板塊:**" not in content and "**市值:**" not in content:
            content = content.replace(
                "## 業務簡介\n",
                "## 業務簡介\n**板塊:** {sector}\n**產業:** {industry}\n**市值:** N/A 百萬台幣\n**企業價值:** N/A 百萬台幣\n\n".format(
                    **meta
                ),
            )

    # Replace business description (preserve metadata block)
    def repl_desc(m):
        return f"{m.group(1)}{new_data['desc']}\n"

    content = re.sub(
        r"(## 業務簡介\n(?:.*?企業價值:.*?\n\n|))(.*?)(?=\n## 供應鏈位置)",
        repl_desc,
        content,
        flags=re.DOTALL,
    )

    # Replace supply chain section
    if "supply_chain" in new_data:
        sc = new_data["supply_chain"] + "\n"
    else:
        sc = f"*   **上游**: {new_data.get('up','')}\n*   **中游**: {new_data.get('mid','')}\n*   **下游**: {new_data.get('down','')}\n"
    content = re.sub(
        r"(## 供應鏈位置\n)(.*?)(?=\n## 主要客戶及供應商)",
        rf"\g<1>{sc}",
        content,
        flags=re.DOTALL,
    )

    # Replace customers/suppliers section
    if "supp" not in new_data:
        ct = new_data["cust"] + "\n"
    else:
        ct = f"### 主要客戶\n*   {new_data['cust']}\n\n### 主要供應商\n*   {new_data['supp']}\n"
    content = re.sub(
        r"(## 主要客戶及供應商\n)(.*?)(?=\n## 財務概況)",
        rf"\g<1>{ct}",
        content,
        flags=re.DOTALL,
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    try:
        print(f"Enriched: {os.path.basename(filepath)}")
    except UnicodeEncodeError:
        print(f"Enriched: ticker {ticker}")


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if not DATA:
        print("DATA dict is empty. Populate it with ticker data before running.")
        return

    count = 0
    for fp in glob.glob(os.path.join(BASE_DIR, "**", "*.md"), recursive=True):
        fn = os.path.basename(fp)
        m = re.search(r"^(\d{4})_", fn)
        if m and m.group(1) in DATA:
            update_file(fp, m.group(1))
            count += 1

    print(f"\nDone. Enriched {count} files.")
    print("REMINDER: Clear the DATA dict now to prevent regressions on next run.")


if __name__ == "__main__":
    main()
