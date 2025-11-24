# 3D Map Setup Guide

## Overview
This update adds a toggleable 3D Globe view using **Globe.gl**, maintaining the existing 2D Google Chart map.

## 1. No API Token Required!
This implementation uses **Globe.gl** and OpenStreetMap/Natural Earth data. 
-   **No Mapbox Token needed.**
-   **No Credit Card needed.**
-   **Completely Free.**

## 2. Features
-   **Toggle Button**: A globe icon switches between 2D and 3D.
-   **3D Globe**: Renders a realistic interactive globe with a starry background.
-   **Data Overlay**: Highlights countries where you have items (Emerald Green).
-   **Tooltips**: Hover over countries to see item counts.
-   **Interactivity**: Click a country to open the detailed list.
-   **Auto-Rotation**: The globe gently rotates until you interact with it.

## 3. Adding Future Map Modes
To add a new mode:
1.  Create `frontend/components/maps/MapNewMode.js`.
2.  Implement a class with `init(containerId, callback)` and `renderData(data)`.
3.  Add the script to `index.html`.
4.  Update the toggle logic in `index.html`.

## 4. Deployment on Render
Simply push the changes. No environment variables or secrets are required for the map.
