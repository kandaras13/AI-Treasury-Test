from __future__ import annotations
import io
import time
import pandas as pd
import streamlit as st

from src.models import ApplicationData
from src.verify import verify_bytes

st.set_page_config(page_title="TTB LabelVerify AI", page_icon="✅", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1180px; padding-top: 1.6rem;}
[data-testid="stMetricValue"] {font-size: 1.7rem;}
.status-pass {padding: .5rem .8rem; border-radius: .5rem; background:#e8f5e9;}
.status-review {padding: .5rem .8rem; border-radius: .5rem; background:#fff8e1;}
.status-fail {padding: .5rem .8rem; border-radius: .5rem; background:#ffebee;}
</style>
""", unsafe_allow_html=True)

st.title("TTB LabelVerify AI")
st.caption("Prototype decision-support tool for alcohol label verification • Standalone • Local OCR • No uploaded files are persisted")

with st.sidebar:
    st.header("How to use")
    st.write("1. Enter the application values.")
    st.write("2. Upload one label image or a batch.")
    st.write("3. Review PASS / REVIEW / FAIL results.")
    st.info("This prototype assists a compliance agent; it does not make a final regulatory decision.")
    mode = st.radio("Review mode", ["Single label", "Batch upload"], horizontal=False)

def app_fields(prefix=""):
    c1, c2 = st.columns(2)
    with c1:
        brand = st.text_input("Brand name *", key=prefix+"brand", placeholder="OLD TOM DISTILLERY")
        ctype = st.text_input("Class / type", key=prefix+"ctype", placeholder="Kentucky Straight Bourbon Whiskey")
        abv_text = st.text_input("Alcohol by volume (ABV %)", key=prefix+"abv", placeholder="45")
    with c2:
        net = st.text_input("Net contents", key=prefix+"net", placeholder="750 mL")
        producer = st.text_input("Bottler / producer", key=prefix+"producer", placeholder="Old Tom Distillery, Louisville, KY")
        country = st.text_input("Country of origin (imports)", key=prefix+"country", placeholder="Optional")
    try:
        abv = float(abv_text) if abv_text.strip() else None
    except ValueError:
        st.error("ABV must be a number, such as 45 or 13.5.")
        abv = None
    return ApplicationData(brand, ctype, abv, net, producer, country)

def render_result(result):
    status_icon = {"PASS":"✅", "REVIEW":"⚠️", "FAIL":"❌"}[result.overall_status]
    st.subheader(f"{status_icon} {result.filename}: {result.overall_status}")
    a,b,c = st.columns(3)
    a.metric("Verification score", f"{result.score:.0f}/100")
    b.metric("OCR confidence", f"{result.ocr_confidence:.0f}%")
    b.caption("OCR confidence is diagnostic, not a compliance score.")
    c.metric("Processing time", f"{result.processing_seconds:.2f}s")
    rows = [f.to_dict() for f in result.fields if f.status != "N/A"]
    st.dataframe(pd.DataFrame(rows)[["field","status","expected","observed","detail"]], use_container_width=True, hide_index=True)
    with st.expander("Show extracted OCR text"):
        st.text(result.extracted_text or "(No text extracted)")

if mode == "Single label":
    st.header("Application values")
    application = app_fields("single_")
    upload = st.file_uploader("Upload label image", type=["png","jpg","jpeg","tif","tiff","webp"])
    if st.button("Verify label", type="primary", disabled=(upload is None or not application.brand_name.strip())):
        with st.spinner("Reading and checking label…"):
            result = verify_bytes(upload.name, upload.getvalue(), application)
        render_result(result)

else:
    st.header("Batch review")
    st.write("For one importer submission with shared application values, enter the values once and upload multiple label images.")
    application = app_fields("batch_")
    uploads = st.file_uploader(
        "Upload label images",
        type=["png","jpg","jpeg","tif","tiff","webp"],
        accept_multiple_files=True
    )
    if uploads:
        st.caption(f"{len(uploads)} file(s) selected.")
    if st.button("Verify batch", type="primary", disabled=(not uploads or not application.brand_name.strip())):
        results = []
        progress = st.progress(0)
        for idx, upload in enumerate(uploads):
            results.append(verify_bytes(upload.name, upload.getvalue(), application))
            progress.progress((idx + 1) / len(uploads))
        df = pd.DataFrame([r.to_row() for r in results])
        st.subheader("Batch results")
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download results CSV", csv, "ttb_label_verification_results.csv", "text/csv")
        pass_count = int((df["overall_status"] == "PASS").sum())
        review_count = int((df["overall_status"] == "REVIEW").sum())
        fail_count = int((df["overall_status"] == "FAIL").sum())
        c1,c2,c3 = st.columns(3)
        c1.metric("Pass", pass_count)
        c2.metric("Needs review", review_count)
        c3.metric("Fail", fail_count)

st.divider()
st.caption("Prototype note: raster OCR cannot reliably prove font weight. The app validates warning wording/capitalization and explicitly asks a human reviewer to confirm the required bold header.")
