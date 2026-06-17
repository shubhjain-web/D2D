# D2D Tool Adoption Dashboard

A single-file interactive dashboard to track **Door-to-Door (D2D) tool adoption** across the RM (Relationship Manager) funnel for Painting Services.

## Overview

This dashboard provides visibility into how the D2D tool is being used throughout the sales funnel — from GRs (General Requests) through Surveys, Quotes, and Hirings — and tracks when D2D links are shared relative to quote creation.

## Features

- **KPI Cards** — Key funnel metrics at a glance (GRs, Surveys, Quotes, Hirings, D2D usage)
- **Funnel Trend Chart** — Daily / Weekly / Monthly view of the full RM funnel
- **Conversion Rates** — Q2S%, H2Q%, H2G% trends over time
- **D2D Adoption Trend** — Stacked chart showing Before Quote vs After Quote D2D usage
- **D2D on Quotes** — Breakdown of how many quotes had a D2D link and when it was used
- **Date Range Filter** — Flexible date filtering across all charts and metrics

## Usage

Just open the HTML file in any browser — no server or dependencies required.

```bash
open D2D_Adoption_Dashboard.html
```

## Tech Stack

- Plain HTML + CSS + JavaScript (no build step)
- [Chart.js](https://www.chartjs.org/) for visualizations

## Data

Currently uses embedded sample data for **June 2026 · Painting Services**. Last updated: Jun 16, 2026.
