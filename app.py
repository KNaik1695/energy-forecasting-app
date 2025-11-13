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
latitude = st.number_input("Latitude (°)", value=45.0, step=0.1)
longitude = st.number_input("Longitude (°)", value=-75.0, step=0.1)
capacity = st.number_input("Installed Capacity (kW)", value=10.0, step=0.1)
COD = st.text_input("COD (yyyy-mm-dd)", value="2025-01-01")
average = st.number_input("PT Static Average (kWh/yr)", value=1500.0, step=0.1)

#%%

if st.button("Predict Energy Output"):
    # Create and run model
    model = SolarEnergyInterpolator()
    case1_vec, case1_total, case2_total, case3_total, case4_total = model.get_solar_energy(latitude, longitude, capacity, COD, average)

    # --- Display scalar results ---
    st.subheader("Model Outputs")
    col1, col2 = st.columns(2)
    with col1:
        st.text("Solar GIS Model Outputs")
        st.metric("1-Year Yield", f"{case1_total/1e3:.2f} MWh")
        st.metric("COD to EOY", f"{case2_total/1e3:.2f} MWh")
    with col2:
        st.text("Regression Model Outputs")
        st.metric("1-Year Yield", f"{case3_total/1e3:.2f} MWh")
        st.metric("COD to EOY", f"{case4_total/1e3:.2f} MWh")

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


# %%
