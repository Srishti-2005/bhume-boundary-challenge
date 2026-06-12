#!/usr/bin/env python3
"""End-to-end village processing — the submission entry point.

Takes a village bundle (input.geojson + imagery.tif [+ boundaries.tif]) and writes
contract-valid predictions.geojson.

Run:
    uv run process_village.py data/34855_vadnerbhairav_chandavad_nashik
    uv run process_village.py input.geojson imagery.tif predictions.geojson
"""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd

from bhume.align import align_plots
from bhume.io import load, write_predictions
from bhume.score import score


def process_village(
    input_geojson_path: str | Path,
    imagery_tif_path: str | Path,
    output_geojson_path: str | Path,
    boundaries_tif_path: str | Path | None = None,
) -> gpd.GeoDataFrame:
    """Process one village and write predictions.geojson.

    Parameters
    ----------
    input_geojson_path:
        Official plot polygons (EPSG:4326).
    imagery_tif_path:
        Georeferenced satellite mosaic.
    output_geojson_path:
        Where to write predictions.
    boundaries_tif_path:
        Optional pre-detected boundary raster.
    """
    plots = gpd.read_file(input_geojson_path)
    plots['plot_number'] = plots['plot_number'].astype(str)

    if boundaries_tif_path is None:
        candidate = Path(input_geojson_path).parent / 'boundaries.tif'
        boundaries_tif_path = candidate if candidate.exists() else None

    preds = align_plots(
        plots=plots,
        imagery_path=imagery_tif_path,
        boundaries_path=boundaries_tif_path,
    )
    write_predictions(output_geojson_path, preds)
    return preds


def main() -> None:
    if len(sys.argv) == 2:
        village_dir = Path(sys.argv[1])
        process_village(
            village_dir / 'input.geojson',
            village_dir / 'imagery.tif',
            village_dir / 'predictions.geojson',
        )
        village = load(village_dir)
        if village.example_truths is not None:
            preds = gpd.read_file(village_dir / 'predictions.geojson')
            print(score(preds, village))
        return

    if len(sys.argv) < 4:
        print(
            'Usage:\n'
            '  uv run process_village.py data/<village_slug>\n'
            '  uv run process_village.py input.geojson imagery.tif predictions.geojson'
        )
        sys.exit(1)

    process_village(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == '__main__':
    main()
