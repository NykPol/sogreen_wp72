"""
This is a boilerplate pipeline 'osm_data_extraction'
generated using Kedro 1.0.0
"""

from kedro.pipeline import Node, Pipeline, node
from .nodes import extract_selected_tags_from_osm_complete


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline([
        node(
            func=extract_selected_tags_from_osm_complete,
            inputs={
                "city_name": "params:city_name",
                "country": "params:country", 
                "tags": "params:osm_tags"
            },
            outputs=["processed_geotags_data", "city_boundary_gdf"],
            name="extract_geotags_node",
        )
    ])
