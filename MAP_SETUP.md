# 3D Map Setup Guide

## Overview
This update adds a toggleable 3D Globe view using Mapbox GL JS, while maintaining the existing 2D Google Chart map.

## 1. Mapbox Token Setup (REQUIRED)
To make the 3D map work, you need a Mapbox Access Token.

1.  **Sign Up**: Go to [mapbox.com](https://www.mapbox.com/) and create a free account.
2.  **Get Token**: Copy your "Default public token" from the dashboard.
3.  **Update Code**:
    -   Open `frontend/index.html`
    -   Find `const MAPBOX_ACCESS_TOKEN = '...';` (around line 2588)
    -   Replace the placeholder with your actual token.
    
    ```javascript
    const MAPBOX_ACCESS_TOKEN = 'pk.eyJ...'; // Your token here
    ```

## 2. Features
-   **Toggle Button**: A globe icon in the map controls switches between 2D and 3D.
-   **3D Globe**: Renders a realistic globe with star atmosphere.
-   **Data Overlay**: Highlights countries where you have items (Emerald Green). Hover to see counts.
-   **Interactivity**: Click a country to open the detailed list (same as 2D map).
-   **Historical Countries**: The map uses a standard modern GeoJSON. Historical items (like USSR) will display if mapped to modern equivalents (e.g., Russia) via the existing `countryAliasMap` logic.

## 3. Adding Future Map Modes
The system is designed to be extensible. To add a new mode (e.g., Heatmap):

1.  **Create Component**: Create `frontend/components/maps/MapHeatmap.js`.
    -   Follow the class structure of `Map3D.js`.
    -   Implement `init(containerId, onClick)` and `renderData(data)`.
2.  **Update HTML**:
    -   Add a container: `<div id="heatmap-container" ...></div>`.
    -   Add a button to the toggle group.
3.  **Update Logic**:
    -   Modify the toggle event listener in `index.html` to handle the new state.
    -   Initialize and render the new map instance.

## 4. Deployment on Render
No special changes needed for Render, as the solution is client-side only.
1.  **Push Changes**: Commit and push the new files (`frontend/components/maps/Map3D.js` and modified `index.html`).
2.  **Environment Variables**: If you prefer not to hardcode the Mapbox token, you can set it as an environment variable in Render, but since this is a static frontend served by Flask, you'd need to inject it into the HTML via `backend/app.py` template rendering.
    -   *Simpler*: Just keep the public token in `index.html`. Mapbox tokens are public by design (restrict them by domain in Mapbox dashboard for security).

## 5. Files Created
-   `frontend/components/maps/Map3D.js`: Core 3D map logic.
-   `frontend/index.html`: Updated with Mapbox libraries and integration logic.

