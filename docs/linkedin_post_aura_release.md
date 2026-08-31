# 🚀 AURA Siting Crafter & GeoLibre WebGIS: Zero-Copy Cloud Lakehouses & In-Browser Spatial Analytics

Can you site a 50ha data center near 330kV lines taking into account slope, riparian veg, and proximity to public spaces as well as requirements for wastewater and thermal discharge, nationally in 5 seconds? 

Well, AURA can. 

The Australian Urban and Regional AI (AURA) Data Center Siting Crafter is a personal learning project that delivers real, practical value for national infrastructure planning. 🇦🇺⚡

Finding optimal, low-risk land for energy-intensive compute hubs, grid interconnects, and clean energy assets traditionally takes months of manual GIS consulting. As an independent learning project, I wanted to explore how modern cloud-native data stacks and client-side compute can transform this into instant, interactive intelligence.

---

### 🌐 How the Journey Unfolded:

• **The Cloud Backbone**: Started with Wherobots Cloud & Apache Sedona to streamline distributed spatial joins and serve as the high-precision lakehouse backbone. 
• **Interactive Public Reporting**: Used my Spatial Report Crafter to turn those lakehouse insights into an interactive report for the public. Check out the guest blog for details: https://blog.wherobots.com/aura-siting-crafter
• **Bridging Web & Desktop GIS**: Next, bridged the lakehouse back into open GIS workflows with **GeoLibre**, thanks to in/giswqs (Prof. Qiusheng Wu). This exposes the spatial data collected and analysed by Wherobots far beyond a traditional desktop GIS stack directly to the browser.

---

### 🕹️ What You Can Do in the App:

• **Explore & Inspect**: Review authentic national data and layer attribution, adjust layer opacity/order, and explore candidate hubs nationally or locally in milliseconds.
• **Ask AI in Plain English**: Ask questions in natural language (*"Show me parcels >50 ha within 5 km of 330kV transmission"*). The query is translated to spatial SQL, executed against the lakehouse, and rendered instantly on the map.
• **Export to Desktop GIS**: Download the declarative GeoLibre JSON project spec to load the entire national model directly into GeoLibre, QGIS, or ArcGIS Pro.

And what did this cost apart from a few late nights? A Google AI monthly subscription to help build the codebase, and Google Cloud free tier credits to host the serverless gateway.

---

### 🙌 Standing on the Shoulders of Giants (Tech Credits):

Massive credit to the open-source communities and platform creators who make modern spatial engineering accessible:
- **GeoLibre & @giswqs (Prof. Qiusheng Wu)** for the open spatial specification and desktop GIS tooling.
- **Wherobots & Apache Sedona** (Jia Yu, Jialin Ding & team) for distributed spatial lakehouse compute and GeoParquet standards.
- **DuckDB Labs & DuckDB-WASM** (Hannes Mühleisen, Mark Raasveldt & team) for client-side analytical SQL in browser memory.
- **MapLibre Team** for performant, open-source WebGL mapping.
- **FastAPI** (Sebastián Ramírez / tiangolo) for clean, high-performance serverless microservices.

---

*Note: This is an independent, personal research project exploring open data and modern cloud-native architectures.*

The full technical architecture and MCDA formulas are documented in the GitHub repository and inside the app's Help modal. Give it a spin and explore the map! 🔗👇

#DataEngineering #SpatialAI #CloudNative #DuckDB #WebGIS #DataCenters #CleanEnergy #Wherobots #ApacheSedona #MapLibre #GeoLibre #OpenSource #OpenData #GIS
