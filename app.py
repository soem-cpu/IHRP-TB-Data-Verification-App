import streamlit as st
import pandas as pd
import importlib.util
import io

st.set_page_config(page_title="Dynamic Rule-Based Data Verification", layout="wide")
st.title("📊 Dynamic Rule-Based Data Verification App")

st.markdown("""
Upload your **Python rules file** and the **Excel file** you want to verify.
The app will dynamically apply the rules and show a validation table.
Each validation result can be downloaded as an Excel file (single sheet).
""")

# Upload rules file (.py)
rules_file = st.file_uploader("Upload your Python rules file (.py)", type=["py"])
if rules_file:
    with open("rules_temp.py", "wb") as f:
        f.write(rules_file.getbuffer())
    spec = importlib.util.spec_from_file_location("rules_module", "rules_temp.py")
    rules_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rules_module)
    st.success("✅ Rules file loaded!")

# Upload Excel data file
data_file = st.file_uploader("Upload Excel file to verify", type=["xlsx", "csv"])
if data_file and rules_file:
    # Preview logic
    if data_file.name.endswith("xlsx"):
        xls = pd.ExcelFile(data_file)
        preview_sheet = xls.sheet_names[0]
        df_preview = xls.parse(preview_sheet)
        st.write(f"Preview of uploaded data (first sheet: {preview_sheet}):")
        st.dataframe(df_preview.head())
    else:
        df_preview = pd.read_csv(data_file)
        st.write("Preview of uploaded data:")
        st.dataframe(df_preview.head())

    # Apply rules
    try:
        results = rules_module.check_rules(data_file)
        if isinstance(results, dict):
            st.markdown("## Validation Results:")
            for k, v in results.items():
                st.write(f"**{k}**")
                if isinstance(v, pd.DataFrame):
                    if not v.empty:
                        st.dataframe(v)
                        # Prepare Excel in-memory for download
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            v.to_excel(writer, index=False, sheet_name=k[:31])
                        st.download_button(
                            label=f"Download {k} as Excel",
                            data=output.getvalue(),
                            file_name=f"{k}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.success(f"No issues found in {k}!")
                else:
                    st.write(v)
        elif isinstance(results, pd.DataFrame):
            if results.empty:
                st.success("✅ No validation issues found!")
            else:
                st.write("Validation results:")
                st.dataframe(results)
                # Download for single frame
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    results.to_excel(writer, index=False, sheet_name="Validation")
                st.download_button(
                    label="Download Validation Results as Excel",
                    data=output.getvalue(),
                    file_name="validation_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.write(results)
    except Exception as e:
        st.error(f"Error running rules: {e}")

st.markdown("---")
st.markdown("Created with Streamlit")
