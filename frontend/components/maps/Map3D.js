/**
 * 3D Globe Map Component using Mapbox GL JS
 * Handles rendering the 3D globe, plotting countries, and interactions.
 */

class Map3D {
    constructor(containerId) {
        this.containerId = containerId;
        this.map = null;
        this.popup = null;
        this.hoveredStateId = null;
        this.isLoaded = false;
        
        // Mapbox Access Token - User needs to replace this!
        // We check if it's defined globally or set it here
        this.accessToken = window.MAPBOX_TOKEN || 'pk.eyJ1Ijoib3NjYXJicmltZWxvdyIsImEiOiJjbTNuZ2Z5cG0wM3E4MmxzNnJtNXJtNXJtIn0.placeholder'; 
    }

    init(onCountryClick) {
        if (this.isLoaded) return;
        
        // Check if mapboxgl is loaded
        if (typeof mapboxgl === 'undefined') {
            console.error('Mapbox GL JS is not loaded.');
            return;
        }

        // Get token from global scope if available (set by user in index.html)
        mapboxgl.accessToken = window.MAPBOX_ACCESS_TOKEN || 'YOUR_MAPBOX_ACCESS_TOKEN_HERE';

        // Create Map
        this.map = new mapboxgl.Map({
            container: this.containerId,
            style: 'mapbox://styles/mapbox/dark-v11', // Dark theme matches the app better
            projection: 'globe', // Enable 3D globe projection
            zoom: 1.5,
            center: [30, 15],
            attributionControl: false
        });

        // Add controls
        this.map.addControl(new mapboxgl.NavigationControl());

        // Add atmosphere styling for star-like background
        this.map.on('style.load', () => {
            this.map.setFog({
                'color': 'rgb(186, 210, 235)', // Lower atmosphere
                'high-color': 'rgb(36, 92, 223)', // Upper atmosphere
                'horizon-blend': 0.02, // Atmosphere thickness (default 0.2 at low zooms)
                'space-color': 'rgb(11, 11, 25)', // Background color
                'star-intensity': 0.6 // Background star brightness (default 0.35 at low zoms )
            });
        });

        this.map.on('load', () => {
            console.log('3D Map Loaded');
            this.isLoaded = true;
            
            // Load Country Borders GeoJSON
            // Using Natural Earth 110m Data hosted via CDN
            this.map.addSource('countries', {
                type: 'geojson',
                data: 'https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_110m_admin_0_countries.geojson',
                generateId: true // Ensure features have IDs for hover state
            });

            // Fill Layer (for coloring countries)
            this.map.addLayer({
                'id': 'country-fills',
                'type': 'fill',
                'source': 'countries',
                'layout': {},
                'paint': {
                    'fill-color': ['case',
                        ['!=', ['feature-state', 'count'], 0], '#10b981', // Green if items > 0 (Emerald-500)
                        '#374151' // Dark Gray if 0 items (Gray-700)
                    ],
                    'fill-opacity': [
                        'case',
                        ['boolean', ['feature-state', 'hover'], false],
                        0.9, // High opacity on hover
                        ['!=', ['feature-state', 'count'], 0], 0.7, // Medium opacity if has items
                        0.3 // Low opacity if empty
                    ]
                }
            });

            // Line Layer (Borders)
            this.map.addLayer({
                'id': 'country-borders',
                'type': 'line',
                'source': 'countries',
                'layout': {},
                'paint': {
                    'line-color': '#9ca3af', // Gray-400
                    'line-width': 1
                }
            });

            // Setup Interactions
            this.setupInteractions(onCountryClick);
            
            // Initial render of data if available
            if (window.collectionData) {
                this.renderData(window.collectionData);
            }
        });
    }

    renderData(collectionData) {
        if (!this.map || !this.map.getSource('countries') || !this.map.isStyleLoaded()) return;

        // Process data to map Country Name -> Item Count
        const countryCounts = {};
        const countryData = {}; // Store sample items for tooltip

        collectionData.forEach(item => {
            // Use the existing helper from index.html
            const countryName = window.getGeoChartCountryName ? window.getGeoChartCountryName(item.country) : item.country;
            
            if (countryName) {
                countryCounts[countryName] = (countryCounts[countryName] || 0) + (item.quantity || 1);
                
                if (!countryData[countryName]) countryData[countryName] = [];
                if (countryData[countryName].length < 5) { // Store first 5 for tooltip
                    countryData[countryName].push(item);
                }
            }
        });

        // We need to match GeoJSON properties to our Data
        // The GeoJSON uses 'name', 'name_long', 'admin' etc.
        // We'll iterate over features and set state.
        // Since we can't easily iterate source features without querying, 
        // we rely on the 'data' being static GeoJSON. 
        // Ideally, we would update the Source data with properties, but 'setFeatureState' is better for interactivity.
        
        // However, to setFeatureState we need feature IDs. The source has generateId: true.
        // We need to find which ID corresponds to which country.
        // Limitation: We can only set state on rendered features or if we know IDs.
        
        // Strategy: Iterate all features in the source (fetch the JSON ourselves to build a map) OR
        // Query rendered features? No, that only works for visible ones.
        
        // Better Strategy: Fetch the GeoJSON once, map names to IDs, then use setFeatureState.
        // Or simpler: Filter the layer paint property using a "match" expression on the 'name' property.
        
        const matchExpression = ['match', ['get', 'name']]; // Start match on 'name' property
        
        // Build the expression: name, color, default
        // We want to color based on 'has items'.
        // But 'setFeatureState' is cleaner for hover. 
        
        // Let's stick to 'setFeatureState' by pre-fetching the GeoJSON to map Names -> IDs.
        // This logic is slightly async.
        
        if (!this.nameIdMap) {
            fetch('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_110m_admin_0_countries.geojson')
                .then(res => res.json())
                .then(data => {
                    this.nameIdMap = {};
                    data.features.forEach((f, i) => {
                        // Map various name fields to the ID (which Mapbox generates as index if we pass it, but here we fetch raw)
                        // Mapbox's 'generateId' uses numeric IDs. We need to ensure they match.
                        // Actually, if we update the source with our own JSON with IDs, it's deterministic.
                        
                        // Let's just update the source data directly with 'count' property!
                        // This is easier than feature-state for static coloring.
                        
                        const name = f.properties.name;
                        const formalName = f.properties.name_long || name;
                        
                        // Try to match our data
                        // We need to handle Aliases in reverse or check both
                        // Our 'countryCounts' keys are normalized (e.g. "United States").
                        // The GeoJSON has "United States".
                        
                        let count = 0;
                        // Check standard name
                        if (countryCounts[name]) count += countryCounts[name];
                        // Check alias mappings if needed (GeoJSON might have "United States of America")
                        
                        // Simple fuzzy check or iterate our counts
                        // Optimization: This loop runs once on load/update.
                        
                        // Let's try to find the count for this feature
                        // We rely on getGeoChartCountryName to have normalized our data to match standard names.
                        // We might need to normalize the GeoJSON name too.
                        
                        const normalizedGeoName = window.getGeoChartCountryName ? window.getGeoChartCountryName(name) : name;
                        count = countryCounts[normalizedGeoName] || 0;
                        
                        // Also check formal name
                        if (count === 0 && f.properties.name_long) {
                             const normalizedFormal = window.getGeoChartCountryName ? window.getGeoChartCountryName(f.properties.name_long) : f.properties.name_long;
                             count = countryCounts[normalizedFormal] || 0;
                        }

                        // Special case: Greenland (owned by Denmark)
                        if (normalizedGeoName === 'Greenland' && countryCounts['Denmark']) {
                            count = countryCounts['Denmark'];
                        }

                        f.properties.itemCount = count;
                        f.id = i; // Set ID for feature state (hover)
                    });
                    
                    this.map.getSource('countries').setData(data);
                });
        } else {
            // If map already exists, we would update properties. 
            // For now, lazy fetch is fine.
        }
    }

    setupInteractions(onCountryClick) {
        // Click
        this.map.on('click', 'country-fills', (e) => {
            if (e.features.length > 0) {
                const feature = e.features[0];
                const countryName = feature.properties.name;
                // Use the normalized name for consistency with the rest of the app
                const normalizedName = window.getGeoChartCountryName ? window.getGeoChartCountryName(countryName) : countryName;
                
                if (onCountryClick) {
                    onCountryClick(normalizedName);
                }
            }
        });

        // Hover
        this.map.on('mousemove', 'country-fills', (e) => {
            if (e.features.length > 0) {
                this.map.getCanvas().style.cursor = 'pointer';
                
                if (this.hoveredStateId !== null) {
                    this.map.setFeatureState(
                        { source: 'countries', id: this.hoveredStateId },
                        { hover: false }
                    );
                }
                
                this.hoveredStateId = e.features[0].id;
                
                this.map.setFeatureState(
                    { source: 'countries', id: this.hoveredStateId },
                    { hover: true }
                );

                // Tooltip
                const feature = e.features[0];
                const count = feature.properties.itemCount || 0;
                const name = feature.properties.name;

                if (!this.popup) {
                    this.popup = new mapboxgl.Popup({
                        closeButton: false,
                        closeOnClick: false,
                        className: 'bg-gray-800 text-white rounded shadow-lg'
                    });
                }

                let html = `<div class="font-bold text-sm">${name}</div>`;
                if (count > 0) {
                    html += `<div class="text-xs text-emerald-400">${count} items collected</div>`;
                } else {
                    html += `<div class="text-xs text-gray-400">No items</div>`;
                }

                this.popup.setLngLat(e.lngLat)
                    .setHTML(html)
                    .addTo(this.map);

            }
        });

        // Leave
        this.map.on('mouseleave', 'country-fills', () => {
            this.map.getCanvas().style.cursor = '';
            
            if (this.hoveredStateId !== null) {
                this.map.setFeatureState(
                    { source: 'countries', id: this.hoveredStateId },
                    { hover: false }
                );
            }
            this.hoveredStateId = null;
            
            if (this.popup) {
                this.popup.remove();
            }
        });
    }
    
    resize() {
        if (this.map) {
            this.map.resize();
        }
    }
}

// Export to global scope
window.Map3D = Map3D;

