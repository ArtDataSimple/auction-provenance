import re
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image


# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="Auction Provenance Map",
    page_icon="🎨",
    layout="wide"
)


# -----------------------------
# File paths
# -----------------------------
# CSV is in the root folder, same level as app.py
DATA_PATH = Path("sothebys_christies_limpio.csv")

# Visuals should be inside a folder called visuals/
VISUALS_DIR = Path("visuals")


# -----------------------------
# Helper functions
# -----------------------------
def classify_provenance(text: str) -> str:
    t = str(text).lower()

    if "estate" in t:
        return "Estate"

    if (
        "familia" in t
        or "famila" in t
        or "family" in t
        or "fishman" in t
        or "maharam" in t
        or "gattorno" in t
    ):
        return "Family Collection"

    if "saul" in t or "ellyn" in t or "marilyn arison" in t:
        return "Named Collector"

    if "fundación" in t or "fundacion" in t or "foundation" in t:
        return "Foundation / Other"

    return "Other / none"


def parse_estimate(estimate: str):
    numbers = re.findall(r"\d[\d,]*", str(estimate))
    numbers = [int(n.replace(",", "")) for n in numbers]

    if len(numbers) >= 2:
        return numbers[0], numbers[1]

    if len(numbers) == 1:
        return numbers[0], numbers[0]

    return None, None


def money_short(value):
    if pd.isna(value):
        return ""

    value = float(value)

    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"

    return f"${value / 1000:.0f}K"


@st.cache_data
def load_data():
    if not DATA_PATH.exists():
        st.error(f"CSV file not found at: {DATA_PATH}")
        st.write("Files Streamlit can see:")
        st.write(list(Path(".").rglob("*")))
        st.stop()

    df = pd.read_csv(DATA_PATH)

    df["Provenance type"] = df["Procedencia"].apply(classify_provenance)

    df[["Low estimate", "High estimate"]] = df["Estimado"].apply(
        lambda x: pd.Series(parse_estimate(x))
    )

    df["Mid estimate"] = (df["Low estimate"] + df["High estimate"]) / 2

    return df


# -----------------------------
# Load data
# -----------------------------
df = load_data()


# -----------------------------
# Header
# -----------------------------
st.title("Auction Provenance Map")
st.subheader("How ownership history becomes market value")

st.markdown(
    """
This app explores a small dataset of selected works from **Sotheby’s and Christie’s**, 
focused on named provenance, estates, family collections, and named collectors.

The central idea: **provenance is not only a catalog detail — it can reduce uncertainty, 
create trust, and turn ownership history into economic value.**
"""
)


# -----------------------------
# Key metrics
# -----------------------------
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Works", len(df))
col2.metric("Auction houses", df["Casa de subastas"].nunique())
col3.metric("Estate works", (df["Provenance type"] == "Estate").sum())
col4.metric(
    "Family collection works",
    (df["Provenance type"] == "Family Collection").sum()
)
col5.metric("Highest estimate", money_short(df["High estimate"].max()))


# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")

selected_house = st.sidebar.multiselect(
    "Auction house",
    options=sorted(df["Casa de subastas"].dropna().unique()),
    default=sorted(df["Casa de subastas"].dropna().unique())
)

selected_provenance = st.sidebar.multiselect(
    "Provenance type",
    options=sorted(df["Provenance type"].dropna().unique()),
    default=sorted(df["Provenance type"].dropna().unique())
)

selected_artist = st.sidebar.multiselect(
    "Artist",
    options=sorted(df["Artista"].dropna().unique()),
    default=sorted(df["Artista"].dropna().unique())
)

filtered = df[
    df["Casa de subastas"].isin(selected_house)
    & df["Provenance type"].isin(selected_provenance)
    & df["Artista"].isin(selected_artist)
].copy()


# -----------------------------
# Tabs
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Visuals", "Dataset", "Article angle"]
)


# -----------------------------
# Tab 1: Overview
# -----------------------------
with tab1:
    st.header("Overview")

    st.markdown(
        """
The dataset shows that only a subset of works carry named provenance, estate, 
or family-collection language. This suggests that named provenance is used selectively, 
especially when ownership history can strengthen the object’s market narrative.
"""
    )

    overview_columns = [
        "Procedencia",
        "Artista",
        "Provenance type",
        "Casa de subastas",
        "Fecha",
        "Estimado",
        "Low estimate",
        "High estimate",
        "Mid estimate",
    ]

    st.dataframe(
        filtered[overview_columns],
        use_container_width=True,
        hide_index=True
    )


# -----------------------------
# Tab 2: Visuals
# -----------------------------
with tab2:
    st.header("Publication visuals")

    st.markdown(
        """
These visuals were created from the CSV dataset and can be used as a companion 
to the article.
"""
    )

    visual_files = [
        "auction_provenance_map_visual_table_portrait_refined_grouped_by_provenance.png",
        "01_named_provenance_breakdown_editorial_fixed_no_subtitle.png",
        "02_estimate_ranges_by_work_editorial_fixed.png",
        "03_auction_house_provenance_mix_editorial_fixed.png",
        "04_average_midpoint_estimate_by_provenance_type_editorial_fixed.png",
    ]

    for file_name in visual_files:
        image_path = VISUALS_DIR / file_name

        if image_path.exists():
            st.image(Image.open(image_path), use_container_width=True)
        else:
            st.warning(f"Missing visual: {file_name}")


# -----------------------------
# Tab 3: Dataset
# -----------------------------
with tab3:
    st.header("Full dataset")

    st.download_button(
        label="Download filtered dataset as CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_provenance_dataset.csv",
        mime="text/csv"
    )

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )


# -----------------------------
# Tab 4: Article angle
# -----------------------------
with tab4:
    st.header("Article angle")

    st.markdown(
        """
### Core thesis

In high-end auctions, named provenance works like a **reputation premium**:  
a named estate, family collection, or known collector can transform an artwork 
from an isolated object into part of a larger cultural and economic story.

### Key idea

**Provenance turns ownership history into economic value.**

### Why it matters

A buyer is not only purchasing an artwork.  
They are also purchasing a story that they hope the next buyer will recognize, trust, and value.

### Behavioral economics logic

Provenance can:

- reduce uncertainty,
- increase trust,
- strengthen the object’s narrative,
- support future resale confidence,
- and create a fresh-to-market effect when works come from estates.

### Important caveat

Provenance alone does not create value. Artist, quality, rarity, condition, 
subject matter, market timing, and estimate strategy still matter.
"""
    )
