"""
Logistics & Supply Chain Operations MIS Dashboard
---------------------------------------------------
A portfolio analytics project simulating a manufacturing company's
plant-to-destination dispatch and delivery operations across India.

Run with:
    streamlit run dashboard/app.py

All figures are calculated live from data/logistics_transactions.csv.
No KPI values are hard-coded.
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# PAGE CONFIG & STYLE
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Logistics & Supply Chain Operations MIS",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#0F3D5C"
STEEL = "#3E6E8E"
SLATE = "#6E8CA0"
AMBER = "#D98E04"
RUST = "#C05B34"
FOG = "#EFF3F5"
INK = "#1B2733"

PALETTE = [NAVY, STEEL, AMBER, RUST, SLATE, "#7FA07A", "#9C7CB4", "#B5A15C"]

CUSTOM_CSS = f"""
<style>
    .main {{
        background-color: #FBFCFD;
    }}
    #MainMenu, footer {{visibility: hidden;}}
    h1, h2, h3 {{
        color: {INK};
        font-family: 'Georgia', 'Cambria', serif;
    }}
    .kpi-card {{
        background-color: white;
        border: 1px solid #E2E8ED;
        border-left: 4px solid {NAVY};
        border-radius: 4px;
        padding: 14px 16px;
        margin-bottom: 8px;
    }}
    .kpi-label {{
        font-size: 12.5px;
        color: #5A6B7A;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    }}
    .kpi-value {{
        font-size: 24px;
        font-weight: 700;
        color: {INK};
    }}
    .kpi-sub {{
        font-size: 12px;
        color: #8A97A3;
        margin-top: 2px;
    }}
    .section-note {{
        background-color: {FOG};
        border-radius: 4px;
        padding: 10px 14px;
        font-size: 14px;
        color: {INK};
        margin: 6px 0 16px 0;
    }}
    div[data-testid="stMetricValue"] {{
        color: {NAVY};
    }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    font=dict(family="Helvetica, Arial, sans-serif", color=INK, size=13),
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=10, r=10, t=45, b=10),
    title_font=dict(size=15, color=INK),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


def style_fig(fig, height=380):
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    fig.update_xaxes(gridcolor="#EAEEF1", zeroline=False)
    fig.update_yaxes(gridcolor="#EAEEF1", zeroline=False)
    return fig


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


@st.cache_data
def load_data():
    df = pd.read_csv(
        os.path.join(DATA_DIR, "logistics_transactions.csv"),
        keep_default_na=False,
        na_values=[""],
    )
    date_cols = ["Dispatch_Date", "Expected_Delivery_Date", "Actual_Delivery_Date"]
    for c in date_cols:
        df[c] = pd.to_datetime(df[c])
    dt_cols = ["Loading_Start_Time", "Loading_End_Time", "Weighbridge_Time", "Gate_Out_Time"]
    for c in dt_cols:
        df[c] = pd.to_datetime(df[c])

    # Derived fields used across the dashboard
    df["Delivery_Days"] = (df["Actual_Delivery_Date"] - df["Dispatch_Date"]).dt.days.clip(lower=0)
    df["Dispatch_Month"] = df["Dispatch_Date"].dt.to_period("M").dt.to_timestamp()
    df["Dispatch_Month_Label"] = df["Dispatch_Date"].dt.strftime("%b %Y")
    df["Freight_Cost_per_Ton"] = df["Freight_Cost"] / df["Quantity_Tons"]
    df["Freight_Cost_per_KM"] = df["Freight_Cost"] / df["Distance_KM"]
    df["Vehicle_Utilization_Pct"] = (df["Quantity_Tons"] / df["Vehicle_Capacity_Tons"]) * 100
    return df


df_raw = load_data()

# ---------------------------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------------------------

st.sidebar.markdown("## Filters")

min_date, max_date = df_raw["Dispatch_Date"].min(), df_raw["Dispatch_Date"].max()
date_range = st.sidebar.date_input(
    "Dispatch Date Range",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)

def multiselect_all(label, options):
    return st.sidebar.multiselect(label, options, default=[])

plant_sel = multiselect_all("Plant", sorted(df_raw["Plant_Name"].unique()))
dest_sel = multiselect_all("Destination", sorted(df_raw["Destination"].unique()))
route_sel = multiselect_all("Route", sorted(df_raw["Route"].unique()))
product_sel = multiselect_all("Product", sorted(df_raw["Product_Name"].unique()))
transporter_sel = multiselect_all("Transporter", sorted(df_raw["Transporter_Name"].unique()))
vtype_sel = multiselect_all("Vehicle Type", sorted(df_raw["Vehicle_Type"].unique()))
status_sel = multiselect_all("Delivery Status", sorted(df_raw["Delivery_Status"].unique()))

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<span style='font-size:12px;color:#8A97A3;'>"
    "Fictional dataset · Logistics & Supply Chain MIS portfolio project"
    "</span>",
    unsafe_allow_html=True,
)

df = df_raw.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_d, end_d = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    df = df[(df["Dispatch_Date"] >= start_d) & (df["Dispatch_Date"] <= end_d)]
if plant_sel:
    df = df[df["Plant_Name"].isin(plant_sel)]
if dest_sel:
    df = df[df["Destination"].isin(dest_sel)]
if route_sel:
    df = df[df["Route"].isin(route_sel)]
if product_sel:
    df = df[df["Product_Name"].isin(product_sel)]
if transporter_sel:
    df = df[df["Transporter_Name"].isin(transporter_sel)]
if vtype_sel:
    df = df[df["Vehicle_Type"].isin(vtype_sel)]
if status_sel:
    df = df[df["Delivery_Status"].isin(status_sel)]

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------

st.markdown(
    f"<h1 style='margin-bottom:0;'>Logistics &amp; Supply Chain Operations MIS</h1>"
    f"<div style='color:#5A6B7A;font-size:15px;margin-top:2px;margin-bottom:18px;'>"
    f"Plant dispatch to customer delivery — performance, cost and reliability monitoring "
    f"across {df_raw['Plant_Name'].nunique()} plants and {df_raw['Destination'].nunique()} destinations</div>",
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("No trips match the selected filters. Adjust the filters in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI CALCULATIONS (computed live from the filtered dataframe — nothing hard-coded)
# ---------------------------------------------------------------------------

def safe_div(a, b):
    return a / b if b else 0.0

total_trips = len(df)
total_qty = df["Quantity_Tons"].sum()
total_freight = df["Freight_Cost"].sum()
on_time_trips = (df["Delivery_Status"] == "On Time").sum()
on_time_pct = safe_div(on_time_trips, total_trips) * 100
avg_delivery_days = df["Delivery_Days"].mean()
avg_delay_days = df.loc[df["Delivery_Status"] == "Delayed", "Delay_Days"].mean()
avg_delay_days = 0 if pd.isna(avg_delay_days) else avg_delay_days
avg_distance = df["Distance_KM"].mean()
freight_per_ton = safe_div(total_freight, total_qty)
freight_per_km = safe_div(total_freight, df["Distance_KM"].sum())
vehicle_util_pct = df["Vehicle_Utilization_Pct"].mean()

kpi_cols = st.columns(5)
kpi_defs = [
    ("Total Trips", f"{total_trips:,}", "Completed dispatch-to-delivery trips"),
    ("Dispatch Qty (Tons)", f"{total_qty:,.0f}", "Total material dispatched"),
    ("Total Freight Cost", f"₹{total_freight:,.0f}", "Sum of freight billed"),
    ("On-Time Delivery %", f"{on_time_pct:,.1f}%", f"{on_time_trips:,} of {total_trips:,} trips"),
    ("Freight Cost / Ton", f"₹{freight_per_ton:,.0f}", "Total freight ÷ total tons"),
]
for col, (label, value, sub) in zip(kpi_cols, kpi_defs):
    col.markdown(
        f"<div class='kpi-card'><div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}</div><div class='kpi-sub'>{sub}</div></div>",
        unsafe_allow_html=True,
    )

kpi_cols2 = st.columns(5)
kpi_defs2 = [
    ("Avg. Delivery Time", f"{avg_delivery_days:,.1f} days", "Dispatch to actual delivery"),
    ("Avg. Delay (Delayed Trips)", f"{avg_delay_days:,.1f} days", "Among delayed trips only"),
    ("Avg. Distance", f"{avg_distance:,.0f} km", "Per trip"),
    ("Freight Cost / KM", f"₹{freight_per_km:,.1f}", "Total freight ÷ total distance"),
    ("Vehicle Utilization %", f"{vehicle_util_pct:,.1f}%", "Loaded qty ÷ vehicle capacity"),
]
for col, (label, value, sub) in zip(kpi_cols2, kpi_defs2):
    col.markdown(
        f"<div class='kpi-card'><div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}</div><div class='kpi-sub'>{sub}</div></div>",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------

tabs = st.tabs([
    "Executive Overview", "Dispatch Performance", "Delivery Performance",
    "Transporter Performance", "Route Analysis", "Cost Analysis",
    "Vehicle Utilization", "Delay Analysis",
])

# ============================ A. EXECUTIVE OVERVIEW =========================
with tabs[0]:
    monthly = df.groupby("Dispatch_Month").agg(
        Trips=("Trip_ID", "count"),
        Dispatch_Qty=("Quantity_Tons", "sum"),
        Freight_Cost=("Freight_Cost", "sum"),
        On_Time_Pct=("On_Time_Flag", "mean"),
    ).reset_index()
    monthly["On_Time_Pct"] *= 100
    monthly["Month_Label"] = monthly["Dispatch_Month"].dt.strftime("%b %Y")

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(monthly, x="Month_Label", y="Dispatch_Qty",
                      title="Monthly Dispatch Volume (Tons)",
                      color_discrete_sequence=[NAVY])
        fig.update_layout(xaxis_title="", yaxis_title="Tons")
        st.plotly_chart(style_fig(fig), use_container_width=True)
    with c2:
        fig = px.line(monthly, x="Month_Label", y="Trips", markers=True,
                       title="Monthly Trip Count", color_discrete_sequence=[STEEL])
        fig.update_layout(xaxis_title="", yaxis_title="Trips")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        fig = px.area(monthly, x="Month_Label", y="Freight_Cost",
                       title="Monthly Freight Cost (₹)", color_discrete_sequence=[AMBER])
        fig.update_traces(line=dict(color=AMBER))
        fig.update_layout(xaxis_title="", yaxis_title="Freight Cost (₹)")
        st.plotly_chart(style_fig(fig), use_container_width=True)
    with c4:
        plant_vol = df.groupby("Plant_Name")["Quantity_Tons"].sum().sort_values(ascending=True).reset_index()
        fig = px.bar(plant_vol, x="Quantity_Tons", y="Plant_Name", orientation="h",
                     title="Dispatch Volume by Plant (Tons)", color_discrete_sequence=[NAVY])
        fig.update_layout(xaxis_title="Tons", yaxis_title="")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    # Executive insights (computed, not invented)
    top_plant = df.groupby("Plant_Name")["Quantity_Tons"].sum().idxmax()
    top_plant_share = df.groupby("Plant_Name")["Quantity_Tons"].sum().max() / total_qty * 100
    best_month = monthly.loc[monthly["Dispatch_Qty"].idxmax(), "Month_Label"]
    worst_ontime_month = monthly.loc[monthly["On_Time_Pct"].idxmin(), "Month_Label"]
    worst_ontime_val = monthly["On_Time_Pct"].min()

    st.markdown(
        f"<div class='section-note'>"
        f"<b>{top_plant}</b> accounts for the highest dispatch share at {top_plant_share:.1f}% of total tonnage. "
        f"<b>{best_month}</b> recorded the highest monthly dispatch volume. "
        f"On-time delivery performance was weakest in <b>{worst_ontime_month}</b> at {worst_ontime_val:.1f}%."
        f"</div>", unsafe_allow_html=True,
    )

# ============================ B. DISPATCH PERFORMANCE ========================
with tabs[1]:
    c1, c2 = st.columns(2)
    with c1:
        prod_qty = df.groupby("Product_Name")["Quantity_Tons"].sum().sort_values(ascending=True).reset_index()
        fig = px.bar(prod_qty, x="Quantity_Tons", y="Product_Name", orientation="h",
                     title="Dispatch Volume by Product (Tons)", color_discrete_sequence=[STEEL])
        fig.update_layout(xaxis_title="Tons", yaxis_title="")
        st.plotly_chart(style_fig(fig), use_container_width=True)
    with c2:
        dest_qty = df.groupby("Destination")["Quantity_Tons"].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(dest_qty, x="Destination", y="Quantity_Tons",
                     title="Top 10 Destinations by Dispatch Volume (Tons)", color_discrete_sequence=[NAVY])
        fig.update_layout(xaxis_title="", yaxis_title="Tons")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        plant_trips = df.groupby("Plant_Name")["Trip_ID"].count().sort_values(ascending=True).reset_index()
        plant_trips.columns = ["Plant_Name", "Trips"]
        fig = px.bar(plant_trips, x="Trips", y="Plant_Name", orientation="h",
                     title="Trip Count by Plant", color_discrete_sequence=[AMBER])
        fig.update_layout(xaxis_title="Trips", yaxis_title="")
        st.plotly_chart(style_fig(fig), use_container_width=True)
    with c4:
        monthly_plant = df.groupby(["Dispatch_Month", "Plant_Name"])["Quantity_Tons"].sum().reset_index()
        monthly_plant["Month_Label"] = monthly_plant["Dispatch_Month"].dt.strftime("%b %Y")
        fig = px.line(monthly_plant, x="Month_Label", y="Quantity_Tons", color="Plant_Name",
                      title="Monthly Dispatch Volume by Plant", color_discrete_sequence=PALETTE)
        fig.update_layout(xaxis_title="", yaxis_title="Tons")
        st.plotly_chart(style_fig(fig), use_container_width=True)

# ============================ C. DELIVERY PERFORMANCE =========================
with tabs[2]:
    c1, c2 = st.columns(2)
    with c1:
        status_counts = df["Delivery_Status"].value_counts().reset_index()
        status_counts.columns = ["Delivery_Status", "Trips"]
        fig = px.pie(status_counts, names="Delivery_Status", values="Trips", hole=0.55,
                     title="On-Time vs Delayed Deliveries",
                     color="Delivery_Status",
                     color_discrete_map={"On Time": NAVY, "Delayed": RUST})
        st.plotly_chart(style_fig(fig), use_container_width=True)
    with c2:
        fig = px.line(monthly, x="Month_Label", y="On_Time_Pct", markers=True,
                      title="Monthly On-Time Delivery %", color_discrete_sequence=[NAVY])
        fig.add_hline(y=on_time_pct, line_dash="dot", line_color=SLATE,
                      annotation_text=f"Overall: {on_time_pct:.1f}%")
        fig.update_layout(xaxis_title="", yaxis_title="On-Time %")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        reason_counts = df.loc[df["Delivery_Status"] == "Delayed", "Delay_Reason"].value_counts().reset_index()
        reason_counts.columns = ["Delay_Reason", "Trips"]
        fig = px.bar(reason_counts.sort_values("Trips"), x="Trips", y="Delay_Reason", orientation="h",
                     title="Delay Reason Distribution", color_discrete_sequence=[RUST])
        fig.update_layout(xaxis_title="Delayed Trips", yaxis_title="")
        st.plotly_chart(style_fig(fig), use_container_width=True)
    with c4:
        fig = px.histogram(df, x="Delivery_Days", nbins=20,
                            title="Distribution of Delivery Time (Days)",
                            color_discrete_sequence=[STEEL])
        fig.update_layout(xaxis_title="Delivery Days (Dispatch → Delivery)", yaxis_title="Trips")
        st.plotly_chart(style_fig(fig), use_container_width=True)

# ============================ D. TRANSPORTER PERFORMANCE ======================
with tabs[3]:
    tp = df.groupby("Transporter_Name").agg(
        Trips=("Trip_ID", "count"),
        On_Time_Pct=("On_Time_Flag", "mean"),
        Freight_Cost=("Freight_Cost", "sum"),
        Avg_Delay=("Delay_Days", "mean"),
    ).reset_index()
    tp["On_Time_Pct"] *= 100
    tp = tp.sort_values("Trips", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(tp.sort_values("Trips"), x="Trips", y="Transporter_Name", orientation="h",
                     title="Transporter-wise Trip Count", color_discrete_sequence=[NAVY])
        fig.update_layout(xaxis_title="Trips", yaxis_title="", height=520)
        st.plotly_chart(style_fig(fig, height=520), use_container_width=True)
    with c2:
        tp_sorted = tp.sort_values("On_Time_Pct")
        fig = px.bar(tp_sorted, x="On_Time_Pct", y="Transporter_Name", orientation="h",
                     title="Transporter-wise On-Time Delivery %", color_discrete_sequence=[STEEL])
        fig.add_vline(x=on_time_pct, line_dash="dot", line_color=SLATE)
        fig.update_layout(xaxis_title="On-Time %", yaxis_title="", height=520)
        st.plotly_chart(style_fig(fig, height=520), use_container_width=True)

    fig = px.bar(tp.sort_values("Freight_Cost"), x="Freight_Cost", y="Transporter_Name", orientation="h",
                 title="Transporter-wise Freight Cost (₹)", color_discrete_sequence=[AMBER])
    fig.update_layout(xaxis_title="Freight Cost (₹)", yaxis_title="", height=520)
    st.plotly_chart(style_fig(fig, height=520), use_container_width=True)

    best_tp = tp.loc[tp["Trips"] >= max(5, tp["Trips"].quantile(0.25))].sort_values("On_Time_Pct", ascending=False)
    if not best_tp.empty:
        top_name = best_tp.iloc[0]["Transporter_Name"]
        top_pct = best_tp.iloc[0]["On_Time_Pct"]
        worst_name = best_tp.iloc[-1]["Transporter_Name"]
        worst_pct = best_tp.iloc[-1]["On_Time_Pct"]
        st.markdown(
            f"<div class='section-note'>Among transporters with a meaningful trip volume, "
            f"<b>{top_name}</b> has the strongest on-time performance at {top_pct:.1f}%, while "
            f"<b>{worst_name}</b> trails at {worst_pct:.1f}%.</div>", unsafe_allow_html=True,
        )

# ============================ E. ROUTE ANALYSIS ================================
with tabs[4]:
    route_stats = df.groupby("Route").agg(
        Trips=("Trip_ID", "count"),
        Dispatch_Qty=("Quantity_Tons", "sum"),
        Avg_Delivery_Days=("Delivery_Days", "mean"),
        Delay_Rate=("On_Time_Flag", lambda x: 100 - x.mean() * 100),
        Freight_Cost=("Freight_Cost", "sum"),
        Avg_Distance=("Distance_KM", "mean"),
    ).reset_index()
    route_stats["Freight_per_Ton"] = route_stats["Freight_Cost"] / df.groupby("Route")["Quantity_Tons"].sum().values

    c1, c2 = st.columns(2)
    with c1:
        top_routes = route_stats.sort_values("Dispatch_Qty", ascending=False).head(10).sort_values("Dispatch_Qty")
        fig = px.bar(top_routes, x="Dispatch_Qty", y="Route", orientation="h",
                     title="Top 10 Routes by Dispatch Volume (Tons)", color_discrete_sequence=[NAVY])
        fig.update_layout(xaxis_title="Tons", yaxis_title="")
        st.plotly_chart(style_fig(fig), use_container_width=True)
    with c2:
        delay_routes = route_stats[route_stats["Trips"] >= 5].sort_values("Delay_Rate", ascending=False).head(10).sort_values("Delay_Rate")
        fig = px.bar(delay_routes, x="Delay_Rate", y="Route", orientation="h",
                     title="Top 10 Routes by Delay Rate (%) — min. 5 trips", color_discrete_sequence=[RUST])
        fig.update_layout(xaxis_title="Delay Rate (%)", yaxis_title="")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    longest_routes = route_stats.sort_values("Avg_Delivery_Days", ascending=False).head(10).sort_values("Avg_Delivery_Days")
    fig = px.bar(longest_routes, x="Avg_Delivery_Days", y="Route", orientation="h",
                 title="Top 10 Routes by Average Delivery Time (Days)", color_discrete_sequence=[STEEL])
    fig.update_layout(xaxis_title="Avg. Delivery Days", yaxis_title="")
    st.plotly_chart(style_fig(fig), use_container_width=True)

    slow_route = route_stats.loc[route_stats["Avg_Delivery_Days"].idxmax()]
    risky_routes = route_stats[route_stats["Trips"] >= 5].sort_values("Delay_Rate", ascending=False)
    riskiest = risky_routes.iloc[0] if not risky_routes.empty else None
    note = (f"<b>{slow_route['Route']}</b> has the longest average delivery time at "
            f"{slow_route['Avg_Delivery_Days']:.1f} days.")
    if riskiest is not None:
        note += (f" <b>{riskiest['Route']}</b> shows the highest delay rate among routes with "
                  f"meaningful volume, at {riskiest['Delay_Rate']:.1f}%.")
    st.markdown(f"<div class='section-note'>{note}</div>", unsafe_allow_html=True)

# ============================ F. COST ANALYSIS ==================================
with tabs[5]:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.area(monthly, x="Month_Label", y="Freight_Cost",
                       title="Monthly Freight Cost Trend (₹)", color_discrete_sequence=[AMBER])
        fig.update_traces(line=dict(color=AMBER))
        fig.update_layout(xaxis_title="", yaxis_title="Freight Cost (₹)")
        st.plotly_chart(style_fig(fig), use_container_width=True)
    with c2:
        route_cost = route_stats.sort_values("Freight_per_Ton", ascending=False).head(10).sort_values("Freight_per_Ton")
        fig = px.bar(route_cost, x="Freight_per_Ton", y="Route", orientation="h",
                     title="Top 10 Routes by Freight Cost per Ton (₹)", color_discrete_sequence=[RUST])
        fig.update_layout(xaxis_title="₹ per Ton", yaxis_title="")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    tp_cost = df.groupby("Transporter_Name")["Freight_Cost"].sum().sort_values(ascending=False).head(10).sort_values()
    fig = px.bar(tp_cost.reset_index(), x="Freight_Cost", y="Transporter_Name", orientation="h",
                 title="Top 10 Transporters by Freight Cost (₹)", color_discrete_sequence=[NAVY])
    fig.update_layout(xaxis_title="Freight Cost (₹)", yaxis_title="")
    st.plotly_chart(style_fig(fig), use_container_width=True)

    high_cost_route = route_stats.loc[route_stats["Freight_per_Ton"].idxmax()]
    st.markdown(
        f"<div class='section-note'><b>{high_cost_route['Route']}</b> has the highest freight cost per ton "
        f"at ₹{high_cost_route['Freight_per_Ton']:,.0f}, against an overall average of ₹{freight_per_ton:,.0f} per ton.</div>",
        unsafe_allow_html=True,
    )

# ============================ G. VEHICLE UTILIZATION ============================
with tabs[6]:
    veh_util = df.groupby("Vehicle_Type").agg(
        Trips=("Trip_ID", "count"),
        Avg_Utilization=("Vehicle_Utilization_Pct", "mean"),
        Total_Qty=("Quantity_Tons", "sum"),
    ).reset_index().sort_values("Avg_Utilization")

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(veh_util, x="Avg_Utilization", y="Vehicle_Type", orientation="h",
                     title="Average Vehicle Utilization % by Vehicle Type", color_discrete_sequence=[NAVY])
        fig.update_layout(xaxis_title="Utilization %", yaxis_title="")
        st.plotly_chart(style_fig(fig), use_container_width=True)
    with c2:
        fig = px.bar(veh_util.sort_values("Trips"), x="Trips", y="Vehicle_Type", orientation="h",
                     title="Trips by Vehicle Type", color_discrete_sequence=[STEEL])
        fig.update_layout(xaxis_title="Trips", yaxis_title="")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    veh_level = df.groupby("Vehicle_ID").agg(
        Trips=("Trip_ID", "count"),
        Avg_Utilization=("Vehicle_Utilization_Pct", "mean"),
    ).reset_index().sort_values("Avg_Utilization")
    underutilized = veh_level[veh_level["Avg_Utilization"] < 80]
    fig = px.histogram(veh_level, x="Avg_Utilization", nbins=20,
                        title="Distribution of Average Utilization % Across Vehicles",
                        color_discrete_sequence=[AMBER])
    fig.add_vline(x=80, line_dash="dot", line_color=RUST, annotation_text="80% threshold")
    fig.update_layout(xaxis_title="Avg. Utilization %", yaxis_title="Vehicle Count")
    st.plotly_chart(style_fig(fig), use_container_width=True)

    st.markdown(
        f"<div class='section-note'>{len(underutilized)} of {len(veh_level)} vehicles in the filtered data "
        f"average below 80% capacity utilization per trip, indicating potential for load consolidation.</div>",
        unsafe_allow_html=True,
    )
    with st.expander("View underutilized vehicles (avg. utilization < 80%)"):
        st.dataframe(
            underutilized.merge(vehicles_lookup := df[["Vehicle_ID", "Vehicle_Type", "Transporter_Name"]].drop_duplicates(),
                                 on="Vehicle_ID", how="left")
            .sort_values("Avg_Utilization")
            .rename(columns={"Avg_Utilization": "Avg_Utilization_%"})
            .round(1),
            use_container_width=True, hide_index=True,
        )

# ============================ H. DELAY ANALYSIS ==================================
with tabs[7]:
    c1, c2 = st.columns(2)
    with c1:
        reason_month = df[df["Delivery_Status"] == "Delayed"].groupby(
            ["Dispatch_Month", "Delay_Reason"])["Trip_ID"].count().reset_index()
        reason_month.columns = ["Dispatch_Month", "Delay_Reason", "Trips"]
        reason_month["Month_Label"] = reason_month["Dispatch_Month"].dt.strftime("%b %Y")
        fig = px.bar(reason_month, x="Month_Label", y="Trips", color="Delay_Reason",
                     title="Monthly Delayed Trips by Reason", color_discrete_sequence=PALETTE)
        fig.update_layout(xaxis_title="", yaxis_title="Delayed Trips", barmode="stack")
        st.plotly_chart(style_fig(fig), use_container_width=True)
    with c2:
        reason_plant = df[df["Delivery_Status"] == "Delayed"].groupby(
            ["Plant_Name", "Delay_Reason"])["Trip_ID"].count().reset_index()
        reason_plant.columns = ["Plant_Name", "Delay_Reason", "Trips"]
        fig = px.bar(reason_plant, x="Plant_Name", y="Trips", color="Delay_Reason",
                     title="Delayed Trips by Plant and Reason", color_discrete_sequence=PALETTE)
        fig.update_layout(xaxis_title="", yaxis_title="Delayed Trips", barmode="stack")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    delay_by_days = df[df["Delivery_Status"] == "Delayed"].groupby("Delay_Reason")["Delay_Days"].mean().sort_values().reset_index()
    fig = px.bar(delay_by_days, x="Delay_Days", y="Delay_Reason", orientation="h",
                 title="Average Delay Days by Reason", color_discrete_sequence=[RUST])
    fig.update_layout(xaxis_title="Avg. Delay Days", yaxis_title="")
    st.plotly_chart(style_fig(fig), use_container_width=True)

    top_reason = df.loc[df["Delivery_Status"] == "Delayed", "Delay_Reason"].value_counts()
    if not top_reason.empty:
        st.markdown(
            f"<div class='section-note'><b>{top_reason.index[0]}</b> is the most common cause of delay, "
            f"responsible for {top_reason.iloc[0]} of {int((df['Delivery_Status']=='Delayed').sum())} delayed trips "
            f"in the filtered data.</div>", unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# RAW DATA / MIS SUMMARY
# ---------------------------------------------------------------------------

st.markdown("---")
with st.expander("View filtered trip-level data"):
    st.dataframe(df.drop(columns=["Dispatch_Month", "Dispatch_Month_Label"]), use_container_width=True, hide_index=True)

st.caption(
    "All figures are derived from a fictional, simulated dataset created for portfolio demonstration purposes only. "
    "No real company, customer, or transaction data is used."
)
