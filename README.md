# Logistics & Supply Chain Operations MIS Dashboard

An interactive MIS dashboard that tracks plant-to-destination dispatch and
delivery operations for a fictional Indian manufacturing company, built to
demonstrate operations/logistics analytics and MIS reporting skills.

## Project Overview

The dashboard follows a single dispatch from plant to delivery — plant,
vehicle assignment, loading, weighbridge, transit, and final delivery — and
turns that trail into the KPIs and charts an operations or logistics manager
would use to run the business day to day: how much is being dispatched, how
reliably it's arriving, what it costs, and where the fleet is underused.

## Business Problem

A manufacturing company dispatches material from multiple plants to
destinations across India using third-party transporters and vehicles.
Without a consolidated view, management has no easy way to see delivery
reliability, freight cost trends, transporter performance, or fleet
utilization across hundreds of trips a month — issues surface only after
customer complaints or unexpected cost overruns.

## Objective

Build a single operations dashboard that lets management:

- Monitor dispatch volume, freight cost, and delivery performance
- Compare plants, routes, transporters, and vehicle types
- Identify the routes and causes behind delivery delays
- Spot underutilized vehicles and cost outliers
- Track how logistics performance trends month over month

## Dataset Overview

All data is **synthetic and randomly generated** with logical business
relationships (no real company, customer, or transaction data). The
generation logic lives in [`src/generate_data.py`](src/generate_data.py).

| File | Description | Rows |
|---|---|---|
| `data/logistics_transactions.csv` | Trip-level dispatch-to-delivery transactions | 1,050 |
| `data/plants.csv` | Plant master (ID, name, city, state) | 6 |
| `data/vehicles.csv` | Vehicle master (ID, type, capacity, transporter) | 60 |
| `data/transporters.csv` | Transporter master (ID, name, region) | 18 |
| `data/products.csv` | Product master (ID, name, category) | 8 |

**Coverage:** 6 plants, 12 destination cities, 60 unique plant-destination
routes, 18 transporters, 60 vehicles, 8 products, spanning January–December
2025.

**Key relationships built into the data:**
- Freight cost scales with distance, quantity, and a per-transporter rate factor
- Transit time scales with distance and vehicle type, so longer routes take longer
- Each transporter has a fixed underlying reliability score that drives its delay frequency
- Roughly one-fifth of the fleet is deliberately modeled as chronically under-loaded, to make vehicle utilization analysis meaningful
- Delivery status, delay days, and on-time flag are all recomputed directly from Expected vs. Actual delivery date — a single source of truth, not independently randomized

## Key KPIs

All KPIs are calculated live from the filtered dataset — none are hard-coded.

1. Total Trips
2. Total Dispatch Quantity (Tons)
3. Total Freight Cost
4. On-Time Delivery %
5. Average Delivery Time
6. Average Delay Days (delayed trips)
7. Average Distance
8. Freight Cost per Ton
9. Freight Cost per KM
10. Vehicle Utilization %

## Dashboard Features

- **8 analysis sections:** Executive Overview, Dispatch Performance, Delivery
  Performance, Transporter Performance, Route Analysis, Cost Analysis,
  Vehicle Utilization, and Delay Analysis
- **10 live KPI cards** at the top of the page
- **20+ charts** (bar, line, area, pie, histogram) built with Plotly
- **8 interactive filters:** date range, plant, destination, route, product,
  transporter, vehicle type, and delivery status — every KPI and chart
  updates with the filter selection
- **Computed insight callouts** in each section (e.g. top plant by volume,
  most delay-prone route, most common delay reason) — generated from the
  filtered data, not pre-written text
- Expandable underutilized-vehicle table and filtered raw-data view

## Analysis Areas

- **Dispatch performance** — volume by plant, product, destination, and month
- **Delivery performance** — on-time vs. delayed split, monthly on-time trend, delivery-time distribution
- **Transporter performance** — trip count, on-time %, and freight cost by transporter
- **Route analysis** — top routes by volume, delay rate, and average delivery time
- **Cost analysis** — monthly freight trend, cost per ton by route, cost by transporter
- **Vehicle utilization** — utilization by vehicle type, and a flagged list of vehicles averaging under 80% capacity
- **Delay analysis** — delay reasons by month and by plant, average delay days by reason

## Business Insights

Based on the generated dataset (full date range, all filters cleared):

- **Hyderabad Assembly Unit** has the highest dispatch volume at roughly 9,280 tons, the largest share among the 6 plants.
- Overall on-time delivery performance is **~90%** across 1,050 trips.
- **National Freight Movers** is the strongest-performing transporter among those with meaningful volume (15+ trips), at 100% on-time delivery in this dataset.
- The **Hyderabad–Ahmedabad** route shows the highest delay rate among routes with at least 5 trips.
- The **Ludhiana–Kolkata** route has the longest average delivery time, reflecting its distance.
- **Toll/Checkpoint Delay** and **Route Diversion** are the joint-leading causes of delayed deliveries, but all nine delay reasons occur at broadly similar frequency — no single cause dominates, which points to operational rather than seasonal risk.
- **June 2025** recorded the highest monthly dispatch volume.
- Around one in six vehicles average below 80% capacity utilization per trip, indicating room for load consolidation.

(Exact figures shift slightly with filters — the dashboard is the source of truth; these are headline numbers from the full dataset.)

## Technology Stack

- **Python 3.10+**
- **Pandas / NumPy** — data generation and aggregation
- **Streamlit** — dashboard framework
- **Plotly Express** — charts


## Limitations

- All data is synthetic, generated with a fixed random seed for reproducibility — it does not represent any real company's operations.
- Transit-time and delay modeling are simplified (e.g., average running speed by vehicle type, a single delay-probability factor per transporter) rather than based on real GPS or traffic data.
- The dataset covers one calendar year (2025) and does not model seasonal demand spikes, festivals, or fuel-price fluctuations.
- Distances between plant states and destination cities are approximate, fictional road-distance estimates, not sourced from a mapping API.
