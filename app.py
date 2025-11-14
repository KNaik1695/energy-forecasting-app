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
latitude = st.number_input("Latitude (°)", value=23.546894, step=0.000001, format="%.6f")
longitude = st.number_input("Longitude (°)", value=81.236985, step=0.000001, format="%.6f")
capacity = st.number_input("Installed Capacity (kW)", value=10.0, step=0.1)
COD = st.text_input("COD (yyyy-mm-dd)", value="2025-06-20")
average = st.number_input("PT Static Average (kWh/yr)", value=1520.0, step=0.1)

#%%

if st.button("Predict Energy Output"):
    # Create and run model
    model = SolarEnergyInterpolator()
    case1_vec, case1_total, case2_total, case3_total, case4_total = model.get_solar_energy(latitude, longitude, capacity, COD, average)
    
    # Outputs in order: case1, 2 and 3, 4 are 1-year and COD-to-EOY yields of the GIS and Regression Model respectively
    
    # Actual outputs = 90% of avg of two model output values
    yr_yield = 0.9*0.5*(case1_total + case3_total)
    cod_yield = 0.9*0.5*(case2_total + case4_total)

    # --- Display scalar results ---
    st.subheader("Model Outputs")
    col1, col2 = st.columns(2)
    with col1:
        st.text("1-Year Yield")
        st.metric("Value:", f"{yr_yield/1e3:.2f} MWh")
    with col2:
        st.text("COD to EOY Yield")
        st.metric("Value:", f"{cod_yield/1e3:.2f} MWh")
        
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
        x=alt.X('Month', sort=months, axis=alt.Axis(title='Month')),
        
        # Y-Axis: Use the 'Value' column, ensure it's treated as Quantitative (Q) data
        y=alt.Y('Value', axis=alt.Axis(title='Energy (kWh)')),
        
        # INTERACTIVITY: This is what creates the tooltip on hover
        tooltip=['Month', 'Value'],
        
        # Optional: Set a nice, consistent color
        color=alt.value("#FFD700") 

    ).interactive() # Allows the user to zoom and pan the chart with the mouse

    # Display the chart in Streamlit
    st.altair_chart(chart, use_container_width=True)

#%%
st.subheader("📂 Batch Prediction From CSV")

uploaded_file = st.file_uploader("Upload CSV file with 5 input columns", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Preview of uploaded file:")
    st.dataframe(df.head())

    # Run model instance
    model = SolarEnergyInterpolator() 
    
    # Validate expected columns
    expected_cols = ["latitude", "longitude", "capacity", "COD", "average"]
    if not all(col in df.columns for col in expected_cols):
        st.error(f"CSV must contain these columns: {expected_cols}")
    else:
        if st.button("Run Batch Prediction"):
            results = []

            for _, row in df.iterrows():
                   
                # Run prediction
                case1_vec, case1_total, case2_total, case3_total, case4_total = model.get_solar_energy(latitude, longitude, capacity, COD, average)

                # # Flatten the monthly vector into columns Month_1 ... Month_12
                # month_dict = {f"Month_{i+1}": monthly_vector[i] for i in range(12)}
                
                yr_yield = round(0.9*0.5*1e-3*(case1_total + case3_total),2)
                cod_yield = round(0.9*0.5*1e-3*(case2_total + case4_total),2)

                results.append({
                    "1-year Yield": yr_yield,
                    "COD to EOY": cod_yield,
                    # **month_dict
                })

            # Add results to dataframe
            results_df = pd.DataFrame(results)
            output_df = pd.concat([df.reset_index(drop=True), results_df], axis=1)

            st.success("Batch prediction complete!")
            st.dataframe(output_df.head())

            # Enable CSV download
            csv_data = output_df.to_csv(index=False)
            st.download_button(
                label="Download Results CSV",
                data=csv_data,
                file_name="solar_predictions.csv",
                mime="text/csv"
            )


# %%
