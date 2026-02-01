"""
Pipeline for generating HTML summary reports
"""

from kedro.pipeline import Pipeline, node, pipeline
from .nodes import generate_html_report


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=generate_html_report,
                inputs=["processed_geotags_data", "city_boundary_gdf", "params:city_name", "params:country", "params:osm_tags"],
                outputs="html_report_path",
                name="generate_html_report_node",
            ),
        ]
    )
