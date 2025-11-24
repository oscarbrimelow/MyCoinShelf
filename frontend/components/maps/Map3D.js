/**
 * 3D Globe Map Component using Globe.gl
 * Completely free, open-source 3D globe visualization.
 * No API keys required.
 */

class Map3D {
    constructor(containerId) {
        this.containerId = containerId;
        this.globe = null;
        this.countriesData = null;
        this.collectionData = [];
        this.isLoaded = false;
    }

    init(onCountryClick) {
        if (this.isLoaded) return;
        
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // Fetch World Borders GeoJSON (Free public dataset)
        fetch('https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson')
            .then(res => res.json())
            .then(countries => {
                this.countriesData = countries;
                this.isLoaded = true;
                
                // Initialize Globe
                this.globe = Globe()
                    (container)
                    .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg') // Cool night mode texture
                    .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png') // Starry background
                    .polygonsData(this.countriesData.features)
                    .polygonAltitude(0.01)
                    .polygonCapColor(d => this.getCountryColor(d))
                    .polygonSideColor(() => 'rgba(0, 100, 0, 0.15)')
                    .polygonStrokeColor(() => '#111')
                    .polygonLabel(({ properties: d }) => this.getTooltipContent(d))
                    .onPolygonClick(({ properties: d }) => {
                        // Handle click
                        const countryName = d.NAME || d.name || d.ADMIN;
                        const normalizedName = window.getGeoChartCountryName ? window.getGeoChartCountryName(countryName) : countryName;
                        if (onCountryClick) {
                            onCountryClick(normalizedName);
                        }
                    })
                    .onPolygonHover(hoverD => {
                        this.globe
                            .polygonAltitude(d => d === hoverD ? 0.06 : 0.01)
                            .polygonCapColor(d => d === hoverD ? '#34d399' : this.getCountryColor(d)); // Highlight on hover
                    });

                // Set initial size
                this.resize();
                
                // If data was passed before load, render it now
                if (this.collectionData.length > 0) {
                    this.refreshColors();
                }
                
                // Auto-rotate gently
                this.globe.controls().autoRotate = true;
                this.globe.controls().autoRotateSpeed = 0.5;
                
                // Allow stopping rotation on interaction
                this.globe.controls().addEventListener('start', () => {
                   this.globe.controls().autoRotate = false;
                });
            });
    }

    renderData(data) {
        this.collectionData = data || [];
        if (this.isLoaded && this.globe) {
            this.refreshColors();
        }
    }
    
    refreshColors() {
        // Force update of polygon colors
        if (this.globe) {
             this.globe.polygonCapColor(d => this.getCountryColor(d));
        }
    }

    getCountryColor(feature) {
        const countryName = feature.properties.NAME || feature.properties.name || feature.properties.ADMIN;
        const normalizedName = window.getGeoChartCountryName ? window.getGeoChartCountryName(countryName) : countryName;
        
        // Check if we have items in this country
        const hasItems = this.collectionData.some(item => {
            const itemCountry = window.getGeoChartCountryName ? window.getGeoChartCountryName(item.country) : item.country;
            // Special case for Greenland (mapped to Denmark in 2D map usually)
            if (normalizedName === 'Greenland' && itemCountry === 'Denmark') return true;
            return itemCountry === normalizedName;
        });

        if (hasItems) {
            return '#10b981'; // Emerald-500 (Green)
        } else {
            return 'rgba(200, 200, 200, 0.1)'; // Transparent/Faint Gray
        }
    }

    getTooltipContent(properties) {
        const countryName = properties.NAME || properties.name || properties.ADMIN;
        const normalizedName = window.getGeoChartCountryName ? window.getGeoChartCountryName(countryName) : countryName;
        
        // Calculate counts
        let count = 0;
        this.collectionData.forEach(item => {
            const itemCountry = window.getGeoChartCountryName ? window.getGeoChartCountryName(item.country) : item.country;
            if (itemCountry === normalizedName) {
                count += (item.quantity || 1);
            }
            // Greenland check
            if (normalizedName === 'Greenland' && itemCountry === 'Denmark') {
                count += (item.quantity || 1);
            }
        });

        return `
            <div class="bg-gray-800 text-white p-2 rounded shadow-lg border border-gray-700">
                <div class="font-bold">${countryName}</div>
                ${count > 0 
                    ? `<div class="text-emerald-400 text-sm">${count} items collected</div>` 
                    : `<div class="text-gray-500 text-xs">No items</div>`}
            </div>
        `;
    }

    resize() {
        if (this.globe) {
            const container = document.getElementById(this.containerId);
            if (container) {
                this.globe.width(container.clientWidth);
                this.globe.height(container.clientHeight);
            }
        }
    }
}

// Export to global scope
window.Map3D = Map3D;
