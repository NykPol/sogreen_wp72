"""
Reporting pipeline nodes for generating HTML summary reports
"""
import geopandas as gpd
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_html_report(
    gdf: gpd.GeoDataFrame,
    city_boundary_gdf: gpd.GeoDataFrame,
    city_name: str,
    country: str,
    osm_tags: List[Dict[str, Any]]
) -> str:
    """
    Generate and save HTML report for OSM data extraction.
    
    Args:
        gdf: GeoDataFrame with extracted features
        city_boundary_gdf: GeoDataFrame with city boundary
        city_name: Name of the city
        country: Country name
        osm_tags: List of category dictionaries with tag specifications
        
    Returns:
        Path to saved HTML report
    """
    logger.info(f"Generating HTML report for {city_name}, {country}")
    
    # Calculate statistics
    total_features = len(gdf)
    extraction_date = datetime.now().strftime('%B %d, %Y')
    
    # Count by OSM tag
    tag_counts = gdf['osm_tag'].value_counts().to_dict()
    
    # Count by geometry type
    geom_counts = gdf.geometry.geom_type.value_counts().to_dict()
    
    # Build category mapping dynamically from parameters
    category_mapping = {}
    for category_config in osm_tags:
        category_name = category_config.get("category", "Unknown")
        category_tags = category_config.get("tags", {})
        
        tag_list = []
        for tag_key, tag_values in category_tags.items():
            for tag_spec in tag_values:
                tag_value = tag_spec["value"]
                osm_tag = f"{tag_key}={tag_value}"
                if osm_tag not in tag_list:  # Avoid duplicates
                    tag_list.append(osm_tag)
        
        category_mapping[category_name] = tag_list
    
    logger.info(f"Dynamic category mapping built: {category_mapping}")
    
    # Generate boundary map using the passed city boundary
    boundary_map_html = generate_boundary_map(city_boundary_gdf, city_name)
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SoGreen WP7.2 Summary Report - {city_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #2d6a4f 0%, #40916c 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #2d6a4f;
            border-bottom: 2px solid #52b788;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .section h3 {{
            color: #40916c;
            margin-top: 20px;
        }}
        .toc {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .toc h2 {{
            color: #2d6a4f;
            border-bottom: 2px solid #52b788;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .toc ol {{
            list-style-position: inside;
            padding-left: 20px;
        }}
        .toc li {{
            margin: 8px 0;
            padding: 5px;
        }}
        .toc a {{
            color: #2d6a4f;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
            color: #40916c;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #2d6a4f 0%, #52b788 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #2d6a4f;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .step {{
            background: #f8f9fa;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #52b788;
            border-radius: 4px;
        }}
        .step h4 {{
            margin-top: 0;
            color: #2d6a4f;
        }}
        .step-description {{
            background: white;
            padding: 12px;
            border-radius: 4px;
            margin: 10px 0;
            line-height: 1.8;
        }}
        .entities {{
            margin: 15px 0;
        }}
        .entity {{
            padding: 10px;
            margin: 8px 0;
            border-radius: 4px;
        }}
        .entity-used {{
            background: #fff3cd;
            border-left: 4px solid #f39c12;
        }}
        .entity-produced {{
            background: #d4edda;
            border-left: 4px solid #27ae60;
        }}
        .map-container {{
            margin: 20px 0;
            text-align: center;
        }}
        .map-container iframe {{
            width: 100%;
            height: 600px;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .map-container img {{
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .variable-card {{
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-left: 3px solid #52b788;
            border-radius: 4px;
        }}
        .variable-card h4 {{
            margin: 0 0 10px 0;
            color: #2d6a4f;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SoGreen WP7.2 Summary Report of Selected Geofeatures for {city_name}</h1>
        <p>OpenStreetMap Data Extraction Report | {country}</p>
        <p style="margin-top:6px; font-size:0.95em; opacity:0.9;">Extraction date: {extraction_date}</p>
    </div>

    <div class="toc">
        <h2>Table of Contents</h2>
        <ol>
            <li><a href="#dataset-overview">Dataset Overview</a></li>
            <li><a href="#data-variables">Data Variables</a></li>
            <li><a href="#osm-tag-distribution">OSM Tag Distribution</a></li>
            <li><a href="#geometry-distribution">Geometry Distribution</a></li>
            <li><a href="#processing-steps">Processing Steps</a></li>
        </ol>
    </div>

    <div class="section">
        <h2 id="dataset-overview">📊 Dataset Overview</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Features</div>
                <div class="number">{total_features:,}</div>
            </div>
            <div class="stat-card">
                <div class="label">OSM Tag Types</div>
                <div class="number">{len(tag_counts)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Geometry Types</div>
                <div class="number">{len(geom_counts)}</div>
            </div>
        </div>
"""
    
    if boundary_map_html:
        html += f"""        <div class="map-container">
            {boundary_map_html}
            <p><em>Figure: {city_name} city boundary</em></p>
        </div>
"""
    
    html += """    </div>

    <div class="section">
        <h2 id="data-variables">🗺️ Data Variables</h2>
        
        <div class="variable-card">
            <h4>element</h4>
            <p><strong>Type:</strong> String (categorical)</p>
            <p><strong>Description:</strong> The OpenStreetMap element <em>type</em> for the feature: one of "node", "way", or "relation". This indicates whether the source OSM object is a point (node), a linear/area feature (way), or a relation grouping multiple objects. Use this together with <code>id</code> to reference the original OSM object.</p>
        </div>

        <div class="variable-card">
            <h4>id</h4>
            <p><strong>Type:</strong> Integer or String</p>
            <p><strong>Description:</strong> The OpenStreetMap element identifier (numeric id). When combined with the <code>element</code> value (type), it uniquely identifies the original OSM object (e.g., node/way/relation) and enables traceability back to OSM sources.</p>
        </div>
        
        <div class="variable-card">
            <h4>name</h4>
            <p><strong>Type:</strong> String (nullable)</p>
            <p><strong>Description:</strong> Human-readable name of the feature. Primarily in local language. Used for feature identification and mapping labels.</p>
        </div>
        
        <div class="variable-card">
            <h4>osm_tag</h4>
            <p><strong>Type:</strong> String (Categorical)</p>
            <p><strong>Description:</strong> OpenStreetMap tag in standardized "key=value" format (e.g., "leisure=park", "highway=cycleway"). Used for feature classification and filtering.</p>
        </div>
        
        <div class="variable-card">
            <h4>geometry</h4>
            <p><strong>Type:</strong> Geometry (WGS84 - EPSG:4326)</p>
            <p><strong>Description:</strong> Spatial representation with types: Point, LineString, Polygon, MultiPolygon, or MultiLineString. Used for spatial analysis and mapping.</p>
        </div>
    </div>

    <div class="section">
        <h2 id="osm-tag-distribution">🏷️ OSM Tag Distribution</h2>
        <table>
            <tr>
                <th>Feature Category</th>
                <th>OSM Tag</th>
                <th>Count</th>
            </tr>
"""
    
    # Add rows organized by category
    for category, tags in category_mapping.items():
        first_tag = True
        for tag in tags:
            count = tag_counts.get(tag, 0)
            if count > 0:
                if first_tag:
                    html += f"""            <tr>
                <td rowspan="{sum(1 for t in tags if tag_counts.get(t, 0) > 0)}"><strong>{category}</strong></td>
                <td>{tag}</td>
                <td>{count:,}</td>
            </tr>
"""
                    first_tag = False
                else:
                    html += f"""            <tr>
                <td>{tag}</td>
                <td>{count:,}</td>
            </tr>
"""
    
    html += """        </table>
    </div>

    <div class="section">
        <h2 id="geometry-distribution">Geometry Distribution</h2>
        <table>
            <tr>
                <th>Geometry Type</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
"""
    
    for geom_type, count in sorted(geom_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_features) * 100 if total_features > 0 else 0
        html += f"""            <tr>
                <td><strong>{geom_type}</strong></td>
                <td>{count:,}</td>
                <td>{percentage:.1f}%</td>
            </tr>
"""
    
    html += """        </table>
    </div>

    <div class="section">
        <h2 id="processing-steps">⚙️ Processing Steps</h2>
        
        <div class="step" id="step1">
            <h4>Step 1: Acquire City Boundary Polygon</h4>
            <div class="step-description">Acquire {city_name} city administrative boundary polygon from OpenStreetMap via Nominatim geocoding service. Uses OSMnx geocode_to_gdf() function to query "{city_name}, {country}" and returns a GeoDataFrame containing the city boundary as a Polygon geometry in WGS84 coordinate system (EPSG:4326).</div>
            <div class="entities">
                <div class="entity entity-used">
                    <strong>📥 Input: </strong>Nominatim Geocoding API
                </div>
                <div class="entity entity-produced">
                    <strong>📤 Output: </strong>{city_name} city boundary polygon (GeoDataFrame)
                </div>
            </div>
        </div>
        
        <div class="step" id="step2">
            <h4>Step 2: Extract OSM Features from Polygon</h4>
            <div class="step-description">Extract all OpenStreetMap features within {city_name} boundary matching specified tag combinations across research categories. Uses OSMnx features_from_polygon() to query the Overpass API for features with tags in specified categories. Returns raw GeoDataFrame with all OSM attributes including geometry, tags, and element IDs.</div>
            <div class="entities">
                <div class="entity entity-used">
                    <strong>📥 Input: </strong>{city_name} city boundary polygon
                </div>
                <div class="entity entity-used">
                    <strong>📥 Input: </strong>OSM Overpass API
                </div>
                <div class="entity entity-produced">
                    <strong>📤 Output: </strong>Raw OSM features GeoDataFrame (all attributes)
                </div>
            </div>
        </div>
        
        <div class="step" id="step3">
            <h4>Step 3: Create Standardized OSM Tag Column</h4>
            <div class="step-description">Transform raw OSM data into standardized format by creating osm_tag column. Iterates through each feature to find which tag key-value pair from the extraction criteria is present, then creates a standardized "key=value" string (e.g., "leisure=park", "highway=cycleway"). This normalization enables consistent querying and analysis across diverse feature types.</div>
            <div class="entities">
                <div class="entity entity-used">
                    <strong>📥 Input: </strong>Raw OSM features GeoDataFrame
                </div>
                <div class="entity entity-produced">
                    <strong>📤 Output: </strong>Features with standardized osm_tag column
                </div>
            </div>
        </div>
        
        <div class="step" id="step4">
            <h4>Step 4: Apply Geometry Type Filtering</h4>
            <div class="step-description">Filter features based on semantically appropriate geometry types. Green spaces (parks, forests, water) must be Polygon/MultiPolygon; transportation points (stops, stations) must be Point; paths (cycleways, footways) must be LineString/MultiLineString. This intelligent filtering based on tag VALUES (not keys) ensures data quality by removing geometrically inappropriate features (e.g., parks tagged as points, bus routes tagged as areas). Features with unrecognized tag values or mismatched geometry types are excluded and logged.</div>
            <div class="entities">
                <div class="entity entity-used">
                    <strong>📥 Input: </strong>Features with standardized osm_tag
                </div>
                <div class="entity entity-produced">
                    <strong>📤 Output: </strong>Geometry-filtered features (valid features)
                </div>
            </div>
        </div>
        
        <div class="step" id="step5">
            <h4>Step 5: Extract Core Research Attributes</h4>
            <div class="step-description">Reduce dataset to essential research variables by selecting core attributes: <strong>name</strong> (feature name from OSM, if available), <strong>osm_tag</strong> (standardized category), <strong>element</strong> (OSM element type: node/way/relation), <strong>id</strong> (OSM element numeric identifier), and <strong>geometry</strong> (spatial representation). This preserves traceability to original OSM entities while removing unnecessary OSM metadata and retains all information required for urban analysis.</div>
            <div class="entities">
                <div class="entity entity-used">
                    <strong>📥 Input: </strong>Geometry-filtered features
                </div>
                <div class="entity entity-produced">
                    <strong>📤 Output: </strong>Final clean GeoDataFrame (core attributes + geometry)
                </div>
            </div>
        </div>
        
        <div class="step" id="step6">
            <h4>Step 6: Export Dataset to GeoJSON Format</h4>
            <div class="step-description">Export final dataset to GeoJSON format (RFC 7946 compliant) for interoperability with GIS software and web mapping applications. File saved as {city_name}_geotags.geojson in UTF-8 encoding with WGS84 coordinate system. The GeoJSON format preserves all feature properties (name, osm_tag) and geometry information, enabling use in QGIS, ArcGIS, web maps, and other geospatial tools.</div>
            <div class="entities">
                <div class="entity entity-used">
                    <strong>📥 Input: </strong>Final clean GeoDataFrame
                </div>
                <div class="entity entity-produced">
                    <strong>📤 Output: </strong>{city_name} Urban Features GeoJSON Dataset
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>Report generated by SoGreen WP7.2 OSM Data Extraction Pipeline</p>
        <p>Data © OpenStreetMap contributors, available under the Open Database License (ODbL)</p>
    </div>
</body>
</html>
"""
    
    # Save HTML report to file
    output_dir = Path("data/08_reporting")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{city_name}_summary_report.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.info(f"HTML report saved to {output_file}")
    
    return str(output_file)


def generate_boundary_map(city_boundary_gdf: gpd.GeoDataFrame, city_name: str) -> str:
    """
    Generate a Folium interactive map showing the city boundary.
    
    Args:
        city_boundary_gdf: GeoDataFrame with city boundary
        city_name: Name of the city
        
    Returns:
        HTML string of Folium map
    """
    try:
        import folium
        
        # Get the city boundary geometry
        city_boundary = city_boundary_gdf.geometry.iloc[0]
        
        # Get the centroid for map center
        centroid = city_boundary.centroid
        
        # Create Folium map centered on the city
        m = folium.Map(
            location=[centroid.y, centroid.x],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Add the city boundary with bold black line
        folium.GeoJson(
            city_boundary,
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': 'black',
                'weight': 4,
                'fillOpacity': 0
            },
            tooltip=f"{city_name} boundary"
        ).add_to(m)
        
        # Convert map to HTML string
        map_html = m._repr_html_()
        
        return map_html
    except Exception as e:
        logger.error(f"Failed to generate boundary map: {e}")
        return ""
