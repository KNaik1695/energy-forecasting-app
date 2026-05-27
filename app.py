#%%
import streamlit as st
import altair as alt
import pandas as pd
from GSA_Interpolator import SolarEnergyInterpolator

#%%

st.set_page_config(page_title="Solar Energy Predictor", layout="centered")

st.title("Solar Energy Forecasting")
st.markdown("Enter the site details to estimate solar energy generation potential.")

# --- Input fields ---
col1, col2 = st.columns(2)

with col1:
    latitude = st.number_input("Latitude (°)", value=23.546894, step=0.000001, format="%.6f")
    longitude = st.number_input("Longitude (°)", value=81.236985, step=0.000001, format="%.6f")
    capacity = st.number_input("Installed Capacity (kW)", value=10.0, step=0.1)
    
with col2:
    COD = st.text_input("COD (yyyy-mm-dd)", value="2025-06-20")
    average = st.number_input("PT Static Average (kWh/yr)", value=1520.0, step=0.1)
    PF = st.number_input("Performance Factor (0-1)", value=0.8, step=0.01, format="%0.2f")

#%%

st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #04364e; /* Green background */
        color: white;              /* White text */
        border-radius: 10px;       /* Rounded corners */
    }
    </style>
""", unsafe_allow_html=True)

if st.button("Predict Energy Output"):
    # Create and run model
    model = SolarEnergyInterpolator()
    case1_vec, case1_total, case2_total, case3_total, case4_total = model.get_solar_energy(latitude, longitude, capacity, COD, average)
    
    # Outputs in order: case1, 2 and 3, 4 are 1-year and COD-to-EOY yields of the GIS and Regression Model respectively
    
    # Actual outputs
    yr_yield = PF*case1_total
    cod_yield = PF*case2_total

    # --- Display scalar results ---
    st.subheader("Model Outputs")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("1-Year Yield:", f"{yr_yield/1e3:.2f} MWh")
    with col2:
        st.metric("COD to EOY Yield:", f"{cod_yield/1e3:.2f} MWh")
        
    # --- Display monthly predictions ---

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    df = pd.DataFrame({
        'Month':months,
        'Value':case1_vec,
    })    
        
    df['Month'] = pd.Categorical(df['Month'], categories=months, ordered=True)    
    base = alt.Chart(df).mark_bar(size =20).properties(
    title="Monthly Performance")

    # Encode the chart axes and interactivity
    chart = base.encode(
        # X-Axis: Use the ordered 'Month' column, ensure it's treated as Nominal (N) data
        x=alt.X(
        'Month',
        sort=months,
        axis=alt.Axis(
            title='Month',
            labelColor='#04364e',
            titleColor='#04364e',
            labelFontSize=14,
            titleFontSize=16
        )
        ),
        
        # Y-Axis: Use the 'Value' column, ensure it's treated as Quantitative (Q) data
        y=alt.Y(
        'Value',
        axis=alt.Axis(
            title='Energy (kWh)',
            labelColor='#04364e',
            titleColor='#04364e',
            labelFontSize=14,
            titleFontSize=16
        )
        ),
        
        # INTERACTIVITY: This is what creates the tooltip on hover
        tooltip=['Month', 'Value'],
        
        # Optional: Set a nice, consistent color
        color=alt.value("#04364e") 

    ).interactive() # Allows the user to zoom and pan the chart with the mouse

    # Display the chart in Streamlit
    st.altair_chart(chart, use_container_width=True)

#%% Helper functions for batch analysis

def find_matching_col(df, aliases):
    """
    Finds the first column whose name contains any alias.
    Case-insensitive and supports aliases as part of larger strings.
    Example: 'Latitude (°)' matches 'latitude'.
    """
    cols_lower = {col: str(col).strip().lower() for col in df.columns}

    for alias in aliases:
        alias = alias.lower()
        for original_col, lower_col in cols_lower.items():
            if alias in lower_col:
                return original_col

    return None


def parse_coordinate(value):
    """
    Parses decimal or DMS coordinates with optional cardinal directions.

    Examples:
        49.272059
        '49.272059 N'
        '49.272059° N'
        '49°16'19.4"N'
        '123°7'30"W'
    """
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip().upper()

    sign = 1
    if "S" in s or "W" in s:
        sign = -1

    # Preserve negative sign if explicitly provided
    if s.startswith("-"):
        sign = -1

    # Remove cardinal directions
    for ch in ["N", "S", "E", "W"]:
        s = s.replace(ch, "")

    # Convert DMS symbols to spaces
    for ch in ["°", "º", "'", "’", "′", '"', "″"]:
        s = s.replace(ch, " ")

    s = s.replace(",", " ")

    parts = s.split()
    nums = []

    for part in parts:
        try:
            nums.append(float(part))
        except:
            pass

    if len(nums) == 0:
        return None

    # Decimal degrees
    if len(nums) == 1:
        return sign * abs(nums[0])

    # DMS: degrees, minutes, seconds
    deg = abs(nums[0])
    minutes = nums[1] if len(nums) > 1 else 0
    seconds = nums[2] if len(nums) > 2 else 0

    decimal_degrees = deg + minutes / 60 + seconds / 3600

    return sign * decimal_degrees

#%%
st.subheader("📂 Batch Prediction From CSV")

# --- Global Input fields ---
col1, col2 = st.columns(2)

with col1:
    COD_global = st.text_input("Global COD (yyyy-mm-dd)", value="2025-01-01")
    
with col2:
    PF_global = st.number_input("Global Performance Factor (0-1)", value=0.8, step=0.01, format="%0.2f")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
st.info("""**Required columns**: 'latitude' [°], 'longitude' [°], 'capacity' [kW]  \n**Optional columns**: PF [0-1], COD [any format].  
         (Default/global values used if not site-specific value not provided)""")

if uploaded_file:
    
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            try:
                df = pd.read_csv(uploaded_file, encoding="cp1252")
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding="latin1")

    # -------- Flexible column matching --------
    lat_col = find_matching_col(df, ["latitude", "lat"])
    lon_col = find_matching_col(df, ["longitude", "long", "lon"])
    capacity_col = find_matching_col(df, ["capacity", "cap"])

    pf_col = find_matching_col(df, ["pf", "performance factor"])
    cod_col = find_matching_col(df, ["cod"])
    average_col = find_matching_col(df, ["average", "staticavg", "static average"])
    
    required_cols = ["latitude", "longitude", "capacity"]
    optional_cols = ["PF", "COD", "average"]
    global_vals = [PF_global, COD_global, average]

    missing_cols = []

    if lat_col is None:
        missing_cols.append("latitude / lat")

    if lon_col is None:
        missing_cols.append("longitude / lon / long")

    if capacity_col is None:
        missing_cols.append("capacity / cap")

    if missing_cols:
        st.error(f"CSV must contain these columns: {missing_cols}")

    else:
        # Create standardized columns used by the model
        df["latitude"] = df[lat_col].apply(parse_coordinate)
        df["longitude"] = df[lon_col].apply(parse_coordinate)
        df["capacity"] = pd.to_numeric(df[capacity_col], errors="coerce")

        # Optional columns: use uploaded values if available, otherwise global/default values
        if pf_col is not None:
            df["PF"] = pd.to_numeric(df[pf_col], errors="coerce")
            df["PF"] = df["PF"].fillna(PF_global)
        else:
            df["PF"] = PF_global

        if cod_col is not None:
            df["COD"] = df[cod_col].fillna(COD_global)
        else:
            df["COD"] = COD_global

        if average_col is not None:
            df["average"] = pd.to_numeric(df[average_col], errors="coerce")
            df["average"] = df["average"].fillna(average)
        else:
            df["average"] = average

        # Validate parsed numeric values
        invalid_rows = df[
            df["latitude"].isna() |
            df["longitude"].isna() |
            df["capacity"].isna()
        ]

        if len(invalid_rows) > 0:
            st.error("Some rows have invalid latitude, longitude, or capacity values after parsing.")
            st.dataframe(invalid_rows.head())

        else:
            col1, col2 = st.columns(2)

            with col1:
                st.metric("No. of sites:", f"{len(df)}")
                st.metric("Total Capacity:", f"{df['capacity'].sum():.1f} kW")

            with col2:
                st.write("Preview of uploaded file:")
                st.dataframe(df.head())

            # Run model instance
            model = SolarEnergyInterpolator()
            # Fill in optional columns with global values if missing in df
            for col, val in zip(optional_cols, global_vals):
                if col not in df.columns:
                    df[col] = val
                
            if st.button("Run Batch Prediction"):
                results = []

                for _, row in df.iterrows():
                    
                            
                    # Run prediction
                    case1_vec, case1_total, case2_total, case3_total, case4_total = model.get_solar_energy(
                        row['latitude'], 
                        row['longitude'], 
                        row['capacity'],
                        row['COD'], 
                        row['average'])

                    # # Flatten the monthly vector into columns Month_1 ... Month_12
                    # month_dict = {f"Month_{i+1}": monthly_vector[i] for i in range(12)}
                    
                    yr_yield = round(row['PF']*1e-3*case1_total,2)
                    cod_yield = round(row['PF']*1e-3*case2_total,2)

                    results.append({
                        "1-yearYield [MWh]": yr_yield,
                        "CODtoEOY [MWh]": cod_yield,
                        # **month_dict
                    })

                # Add results to dataframe
                results_df = pd.DataFrame(results)
                output_df = pd.concat([df.reset_index(drop=True), results_df], axis=1)

                st.success("Batch prediction complete!")
                st.write("Columns added:")
                st.dataframe(output_df[["1-yearYield [MWh]","CODtoEOY [MWh]"]].head())

                # Enable CSV download
                csv_data = output_df.to_csv(index=False)
                st.download_button(
                    label="Download Results CSV",
                    data=csv_data,
                    file_name="solar_predictions.csv",
                    mime="text/csv"
                )


# %%
