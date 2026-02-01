"""
This is a boilerplate pipeline 'osm_data_extraction'
generated using Kedro 1.0.0
"""

import osmnx as ox
import pandas as pd
import geopandas as gpd
from typing import Dict, Any, List, Union
import logging

logger = logging.getLogger(__name__)



def extract_selected_tags_from_osm_complete(city_name: str, country: str, tags: List[Dict[str, Any]]) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Extract features from OpenStreetMap for a specified city and return processed GeoDataFrame.
    
    Args:
        city_name: Name of the city
        country: Name of the country
        tags: List of category dictionaries with tag/value/geometry specifications
              Format: [{"category": "...", "tags": {"leisure": [{"value": "park", "geometry": "area"}, ...], ...}}, ...]
    
    Returns:
        Tuple of (processed features GeoDataFrame, city boundary GeoDataFrame)
    """
    logger.info(f"Extracting OSM features for {city_name}, {country}")
    
    # Parse the new parameter structure
    osm_query_tags = {}  # For OSMnx API: {"leisure": ["park", "garden"], ...}
    geometry_lookup = {}  # For filtering: {"leisure=park": "area", "amenity=school": ["point", "area"], ...}
    
    for category_config in tags:
        category_name = category_config.get("category", "Unknown")
        category_tags = category_config.get("tags", {})
        
        for tag_key, tag_values in category_tags.items():
            # Collect values for OSM query
            if tag_key not in osm_query_tags:
                osm_query_tags[tag_key] = []
            
            for tag_spec in tag_values:
                tag_value = tag_spec["value"]
                geometry_spec = tag_spec["geometry"]
                
                # Add to OSM query
                if tag_value not in osm_query_tags[tag_key]:
                    osm_query_tags[tag_key].append(tag_value)
                
                # Build geometry lookup
                osm_tag = f"{tag_key}={tag_value}"
                geometry_lookup[osm_tag] = geometry_spec
    
    logger.info(f"OSM query tags: {osm_query_tags}")
    logger.info(f"Geometry specifications: {geometry_lookup}")
    
    # Get the city boundary
    try:
        city_gdf = ox.geocode_to_gdf(f"{city_name}, {country}")
        logger.info(f"Successfully geocoded {city_name}, {country}")
    except Exception as e:
        logger.error(f"Failed to geocode {city_name}, {country}: {e}")
        raise
    
    # Extract features using the specified tags within the city boundary
    try:
        features_gdf = ox.features_from_polygon(
            city_gdf.geometry.iloc[0], 
            tags=osm_query_tags
        )
        logger.info(f"Found {len(features_gdf)} features in {city_name}")
        
    except Exception as e:
        logger.error(f"Failed to extract features from OSM: {e}")
        raise
    
    # Create osm_tag column based on actual feature tags
    def get_osm_tag(row):
        """Extract the primary OSM tag from the feature."""
        for tag_key in osm_query_tags.keys():
            if tag_key in row.index and pd.notna(row[tag_key]):
                tag_value = row[tag_key]
                return f"{tag_key}={tag_value}"
        return "unknown"
    
    features_gdf['osm_tag'] = features_gdf.apply(get_osm_tag, axis=1)
    
    # Filter geometries based on tag specifications
    unknown_tags = set()
    excluded_by_geometry = set()
    
    def should_keep_feature(row):
        """Determine if feature should be kept based on tag value and geometry type."""
        geom_type = row.geometry.geom_type
        osm_tag = row['osm_tag']
        
        # Handle unknown tags
        if osm_tag == 'unknown' or osm_tag not in geometry_lookup:
            unknown_tags.add(osm_tag)
            return False
        
        # Get allowed geometry types for this tag
        allowed_geometries = geometry_lookup[osm_tag]
        
        # Handle "any" - accept all geometries
        if allowed_geometries == "any":
            return True
        
        # Normalize to list for consistent checking
        if isinstance(allowed_geometries, str):
            allowed_geometries = [allowed_geometries]
        
        # Map geometry types to our specification names
        geometry_type_mapping = {
            "point": ["Point"],
            "area": ["Polygon", "MultiPolygon"],
            "line": ["LineString", "MultiLineString"]
        }
        
        # Check if current geometry matches any allowed type
        for allowed_type in allowed_geometries:
            if geom_type in geometry_type_mapping.get(allowed_type, []):
                return True
        
        # Geometry doesn't match specification
        excluded_by_geometry.add(f"{osm_tag} (geometry: {geom_type})")
        return False
    
    features_gdf = features_gdf[features_gdf.apply(should_keep_feature, axis=1)].copy()
    logger.info(f"After filtering by geometry specifications: {len(features_gdf)} features")
    
    # Log warnings for excluded features
    if unknown_tags:
        logger.warning(f"Excluded features with unknown/unconfigured tags: {unknown_tags}")
    if excluded_by_geometry:
        logger.info(f"Excluded features due to geometry mismatch: {excluded_by_geometry}")
    
    # Select columns for output
    result_columns = []
    
    # Name
    if 'name' in features_gdf.columns:
        result_columns.append('name')
    else:
        features_gdf['name'] = None
        result_columns.append('name')
    
    # Add osm_tag and geometry
    result_columns.extend(['osm_tag', 'geometry'])
    
    # Create final dataframe with required columns
    result_gdf = features_gdf[result_columns].copy()
    
    # Log summary statistics
    logger.info(f"Successfully extracted {len(result_gdf)} features")
    logger.info(f"Features with names: {result_gdf['name'].notna().sum()}")
    logger.info(f"Geometry types: {result_gdf.geometry.geom_type.value_counts().to_dict()}")
    logger.info(f"OSM tag distribution: {result_gdf['osm_tag'].value_counts().to_dict()}")
    
    return result_gdf, city_gdf
