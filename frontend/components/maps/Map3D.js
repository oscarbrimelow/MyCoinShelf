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
        this.resizeAttempts = 0;
    }

    init(onCountryClick) {
        if (this.isLoaded) {
            this.resize();
            return;
        }
        
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error("Map3D: Container not found:", this.containerId);
            return;
        }

        // Show a temporary loading text
        container.innerHTML = '<div class="flex h-full items-center justify-center text-emerald-500">Loading 3D Globe...</div>';

        // Fetch World Borders GeoJSON
        fetch('https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson')
            .then(res => {
                if (!res.ok) throw new Error("Failed to fetch GeoJSON");
                return res.json();
            })
            .then(countries => {
                this.countriesData = countries;
                this.isLoaded = true;
                
                // Clear loading text
                container.innerHTML = '';

                // Initialize Globe
                if (typeof Globe === 'undefined') {
                    console.error("Map3D: Globe.gl library not loaded!");
                    container.innerHTML = '<div class="text-red-500 text-center p-4">Error: 3D Library failed to load. Please refresh.</div>';
                    return;
                }

                try {
                    this.globe = Globe()
                        (container)
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
                            if (onCountryClick) {
                                onCountryClick(normalizedName);
                            }
                        })
                        .onPolygonHover(hoverD => {
                            if (!this.globe) return;
                            this.globe
                                .polygonAltitude(d => d === hoverD ? 0.06 : 0.01)
                                .polygonCapColor(d => d === hoverD ? '#34d399' : this.getCountryColor(d));
                        });

                    // Initial render of data
                    if (this.collectionData.length > 0) {
                        this.refreshColors();
                    }
                    
                    // Auto-rotate
                    this.globe.controls().autoRotate = true;
                    this.globe.controls().autoRotateSpeed = 0.5;
                    this.globe.controls().addEventListener('start', () => {
                       this.globe.controls().autoRotate = false;
                    });

                    // Force resize after init to ensure it fits the now-visible container
                    this.resize();
                    
                    // Retry resize a few times in case of animation/layout delay
                    this.forceResizeLoop();

                } catch (e) {
                    console.error("Map3D: Error initializing globe:", e);
                    container.innerHTML = `<div class="text-red-500 text-center p-4">Error initializing 3D Map: ${e.message}</div>`;
                }
            })
            .catch(err => {
                console.error("Map3D: Network error:", err);
                container.innerHTML = `<div class="text-red-500 text-center p-4">Failed to load map data. Check internet connection.</div>`;
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
            if (itemCountry === normalizedName) {
                count += (item.quantity || 1);
            }
            if (normalizedName === 'Greenland' && itemCountry === 'Denmark') {
                count += (item.quantity || 1);
            }
        });

        return `
            <div class="bg-gray-800 text-white p-2 rounded shadow-lg border border-gray-700 font-sans">
                <div class="font-bold text-sm">${countryName}</div>
                ${count > 0 
                    ? `<div class="text-emerald-400 text-xs font-semibold">${count} items</div>` 
                    : `<div class="text-gray-500 text-xs">No items</div>`}
            </div>
        `;
    }

    resize() {
        if (this.globe) {
            const container = document.getElementById(this.containerId);
            if (container && container.clientWidth > 0 && container.clientHeight > 0) {
                this.globe.width(container.clientWidth);
                this.globe.height(container.clientHeight);
            }
        }
    }
    
    forceResizeLoop() {
        let attempts = 0;
        const interval = setInterval(() => {
            this.resize();
            attempts++;
            if (attempts > 10) clearInterval(interval);
        }, 100);
    }
}

window.Map3D = Map3D;
