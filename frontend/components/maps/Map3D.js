/**
 * 3D Globe Map Component using Globe.gl
 * Completely free, open-source 3D globe visualization.
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
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // 1. Ensure container styles to prevent overflow
        container.style.position = 'relative';
        container.style.width = '100%';
        container.style.height = '100%';
        container.style.overflow = 'hidden';

        // 2. Check size - if 0, wait
        const rect = container.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) {
            setTimeout(() => this.init(onCountryClick), 100);
            return;
        }

        if (this.isLoaded) {
            this.resize();
            return;
        }

        // Show Loading
        container.innerHTML = '<div class="flex h-full items-center justify-center text-emerald-500 font-bold animate-pulse">Loading 3D Globe...</div>';

        // Fetch Data
        fetch('https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson')
            .then(res => res.json())
            .then(countries => {
                this.countriesData = countries;
                this.isLoaded = true;
                container.innerHTML = ''; // Clear loading

                // Initialize Globe with EXPLICIT dimensions
                // This prevents the "massive canvas" issue
                const width = container.clientWidth;
                const height = container.clientHeight;

                this.globe = Globe()
                    (container)
                    .width(width)
                    .height(height)
                    .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
                    .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
                    .polygonsData(this.countriesData.features)
                    .polygonAltitude(0.01)
                    .polygonCapColor(d => this.getCountryColor(d))
                    .polygonSideColor(() => 'rgba(0, 100, 0, 0.15)')
                    .polygonStrokeColor(() => '#111')
                    .polygonLabel(({ properties: d }) => this.getTooltipContent(d))
                    .onPolygonClick(({ properties: d }) => {
                        const countryName = d.NAME || d.name || d.ADMIN;
                        const normalizedName = window.getGeoChartCountryName ? window.getGeoChartCountryName(countryName) : countryName;
                        if (onCountryClick) onCountryClick(normalizedName);
                    })
                    .onPolygonHover(hoverD => {
                        if (!this.globe) return;
                        this.globe
                            .polygonAltitude(d => d === hoverD ? 0.06 : 0.01)
                            .polygonCapColor(d => d === hoverD ? '#34d399' : this.getCountryColor(d));
                    });

                // Render initial data
                if (this.collectionData.length > 0) {
                    this.refreshColors();
                }

                // Setup controls
                this.globe.controls().autoRotate = true;
                this.globe.controls().autoRotateSpeed = 0.5;
                this.globe.controls().enableZoom = true;
                
                // Set initial POV to ensure camera isn't lost
                this.globe.pointOfView({ lat: 20, lng: 0, altitude: 2.5 });

                this.globe.controls().addEventListener('start', () => {
                   this.globe.controls().autoRotate = false;
                });
                
                // Final resize to match container
                this.resize();

            })
            .catch(err => {
                console.error("3D Map Error:", err);
                container.innerHTML = `<div class="text-red-500 p-4 text-center">Failed to load 3D Map.<br><span class="text-xs text-gray-400">${err.message}</span></div>`;
            });
    }

    renderData(data) {
        this.collectionData = data || [];
        if (this.isLoaded && this.globe) {
            this.refreshColors();
        }
    }
    
    refreshColors() {
        if (this.globe) {
             this.globe.polygonCapColor(d => this.getCountryColor(d));
        }
    }

    getCountryColor(feature) {
        const countryName = feature.properties.NAME || feature.properties.name || feature.properties.ADMIN;
        const normalizedName = window.getGeoChartCountryName ? window.getGeoChartCountryName(countryName) : countryName;
        
        const hasItems = this.collectionData.some(item => {
            const itemCountry = window.getGeoChartCountryName ? window.getGeoChartCountryName(item.country) : item.country;
            if (normalizedName === 'Greenland' && itemCountry === 'Denmark') return true;
            return itemCountry === normalizedName;
        });

        return hasItems ? '#10b981' : 'rgba(200, 200, 200, 0.1)';
    }

    getTooltipContent(properties) {
        const countryName = properties.NAME || properties.name || properties.ADMIN;
        const normalizedName = window.getGeoChartCountryName ? window.getGeoChartCountryName(countryName) : countryName;
        
        let count = 0;
        this.collectionData.forEach(item => {
            const itemCountry = window.getGeoChartCountryName ? window.getGeoChartCountryName(item.country) : item.country;
            if (itemCountry === normalizedName) count += (item.quantity || 1);
            if (normalizedName === 'Greenland' && itemCountry === 'Denmark') count += (item.quantity || 1);
        });

        return `
            <div style="background: #1f2937; color: white; padding: 8px; border-radius: 4px; border: 1px solid #374151; font-family: sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                <div style="font-weight: bold; margin-bottom: 4px;">${countryName}</div>
                ${count > 0 
                    ? `<div style="color: #34d399; font-size: 12px;">${count} items</div>` 
                    : `<div style="color: #9ca3af; font-size: 12px;">No items</div>`}
            </div>
        `;
    }

    resize() {
        if (this.globe) {
            const container = document.getElementById(this.containerId);
            if (container) {
                const width = container.clientWidth;
                const height = container.clientHeight;
                if (width > 0 && height > 0) {
                    this.globe.width(width);
                    this.globe.height(height);
                }
            }
        }
    }
}

window.Map3D = Map3D;
