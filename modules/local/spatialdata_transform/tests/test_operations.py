"""Numerical/unit tests for the Part 2 SpatialData operations.

Run from the repository root with the module environment activated, e.g.:

    pytest modules/local/spatialdata_transform/tests/test_operations.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import dask.array as da
import numpy as np
import pytest
import xarray as xr
from dask.base import is_dask_collection
from geopandas import GeoDataFrame
from shapely.geometry import Polygon
from spatialdata import SpatialData
from spatialdata.models import Image2DModel, ShapesModel
from spatialdata.transformations import Identity, get_transformation

# Allow importing the operation module without treating the whole repo as a package.
sys.path.insert(0, str(Path(__file__).parent.parent))

from operations import (  # noqa: E402
    BackgroundCorrectionOperation,
    FilterCellsOperation,
    MergeChannelsOperation,
    OperationError,
    _is_multiscale_image,
)


def _image(channels: list[str], shape: tuple[int, int] = (10, 10), multiscale: bool = False):
    rng = np.random.default_rng(42)
    arr = rng.integers(50, 1000, size=(len(channels), *shape), dtype=np.uint16)
    dask_arr = da.from_array(arr, chunks=(len(channels), *shape[:2]))
    dataarray = xr.DataArray(dask_arr, dims=["c", "y", "x"])
    if multiscale:
        return Image2DModel.parse(
            dataarray,
            c_coords=channels,
            scale_factors=[2, 2],
            transformations={"global": Identity()},
        )
    return Image2DModel.parse(dataarray, c_coords=channels, transformations={"global": Identity()})


def _shapes():
    geoms = [
        Polygon([(0, 0), (3, 0), (3, 3), (0, 3)]),
        Polygon([(4, 4), (5, 4), (5, 5), (4, 5)]),
        Polygon([(6, 6), (8, 6), (8, 8), (6, 8)]),
    ]
    return ShapesModel.parse(GeoDataFrame({"geometry": geoms}))


def _ctx(name: str, args: dict):
    return {"name": name, "stage": "before_image_segmentation", "args": args}


@pytest.mark.parametrize(
    "method, kwargs",
    [
        ("subtract_constant", {"value": 25}),
        ("divide", {"value": 2.0}),
        ("gaussian", {"sigma": 1.0}),
        ("rolling_ball", {"radius": 3}),
        ("tophat", {"radius": 3}),
    ],
)
def test_background_correction_methods(method, kwargs):
    sdata = SpatialData(images={"im": _image(["DAPI", "membrane_a"])})
    ctx = {"args": {"image_key": "im", "channel": "DAPI", "method": method, **kwargs}, "stage": "before_image_segmentation"}
    op = BackgroundCorrectionOperation()
    before = sdata.images["im"].sel(c="DAPI").compute()
    before_unchanged = sdata.images["im"].sel(c="membrane_a").compute()

    op.validate(ctx, sdata)
    sdata2, report = op.apply(sdata, ctx)

    assert is_dask_collection(sdata2.images["im"].data)
    assert report["method"] == method
    assert report["input_dtype"] == "uint16"
    assert report["output_dtype"] == "uint16"

    after = sdata2.images["im"].sel(c="DAPI").compute()
    unchanged = sdata2.images["im"].sel(c="membrane_a").compute()

    assert not np.array_equal(before, after)
    assert np.array_equal(unchanged, before_unchanged)


def test_background_correction_multiscale():
    sdata = SpatialData(images={"im": _image(["DAPI", "membrane_a"], multiscale=True)})
    ctx = {
        "args": {"image_key": "im", "channel": "DAPI", "method": "subtract_constant", "value": 10},
        "stage": "before_image_segmentation",
    }
    BackgroundCorrectionOperation().validate(ctx, sdata)
    sdata2, _ = BackgroundCorrectionOperation().apply(sdata, ctx)

    for scale in sdata2.images["im"].keys():
        da = sdata2.images["im"][scale]["image"]
        assert "DAPI" in da.coords["c"].values
        assert is_dask_collection(da.data)


def test_merge_channels_max():
    arr = np.zeros((3, 4, 4), dtype=np.uint16)
    arr[0] = 10
    arr[1] = 20
    arr[2] = 30
    da = xr.DataArray(arr, dims=["c", "y", "x"])
    im = Image2DModel.parse(da, c_coords=["DAPI", "membrane_a", "membrane_b"], transformations={"global": Identity()})
    sdata = SpatialData(images={"im": im})

    ctx = {
        "args": {"image_key": "im", "channels": ["membrane_a", "membrane_b"]},
        "stage": "before_image_segmentation",
    }
    MergeChannelsOperation().validate(ctx, sdata)
    sdata2, report = MergeChannelsOperation().apply(sdata, ctx)

    merged = sdata2.images["im"].sel(c="combined_membrane").compute()
    assert (merged == 30).all()
    assert list(sdata2.images["im"].coords["c"].values) == ["DAPI", "membrane_a", "membrane_b", "combined_membrane"]
    assert report["method"] == "max"


def test_merge_channels_prod_scaling():
    arr = np.zeros((2, 2, 2), dtype=np.uint16)
    arr[0] = 300
    arr[1] = 300
    da = xr.DataArray(arr, dims=["c", "y", "x"])
    im = Image2DModel.parse(da, c_coords=["a", "b"], transformations={"global": Identity()})
    sdata = SpatialData(images={"im": im})

    ctx = {
        "args": {"image_key": "im", "channels": ["a", "b"], "method": "prod", "output_channel": "prod_ch"},
        "stage": "before_image_segmentation",
    }
    MergeChannelsOperation().validate(ctx, sdata)
    sdata2, _ = MergeChannelsOperation().apply(sdata, ctx)

    expected = min(int(300 * 300 * 65534 / 65535), 65535)
    merged = sdata2.images["im"].sel(c="prod_ch").compute()
    assert (merged == expected).all()


def test_merge_channels_creates_segmentation_image():
    arr = np.zeros((3, 8, 8), dtype=np.uint16)
    arr[0] = 10  # DNA
    arr[1] = 20  # Membrane
    arr[2] = 30  # PanCK
    da = xr.DataArray(arr, dims=["c", "y", "x"])
    da.attrs["custom_source_attr"] = "preserved"
    im = Image2DModel.parse(
        da,
        c_coords=["DNA", "Membrane", "PanCK"],
        scale_factors=[2, 2],
        transformations={"global": Identity()},
    )
    sdata = SpatialData(images={"stitched_image": im})

    ctx = {
        "args": {
            "image_key": "stitched_image",
            "output_image_key": "segmentation_image",
            "channel_groups": {
                "nuclear": ["DNA"],
                "membrane": ["Membrane", "PanCK"],
            },
            "method": "max",
        },
        "stage": "before_image_segmentation",
    }
    MergeChannelsOperation().validate(ctx, sdata)
    sdata2, report = MergeChannelsOperation().apply(sdata, ctx)

    assert "segmentation_image" in sdata2.images
    assert sdata2.attrs.get("cell_segmentation_image") == "segmentation_image"
    assert "stitched_image" in sdata2.images

    seg = sdata2.images["segmentation_image"]
    assert _is_multiscale_image(seg)
    assert list(seg["scale0"]["image"].coords["c"].values) == ["nuclear", "membrane"]
    assert list(seg.keys()) == list(im.keys())

    # nuclear copied exactly; membrane = max(Membrane, PanCK)
    scale0 = seg["scale0"]["image"].compute()
    assert (scale0.sel(c="nuclear") == 10).all()
    assert (scale0.sel(c="membrane") == 30).all()

    # Transformations preserved on the output image
    assert get_transformation(seg, get_all=True) == get_transformation(im, get_all=True)

    # Only the duplicate SpatialData transform attribute was removed; other attrs survive
    assert seg["scale0"]["image"].attrs.get("custom_source_attr") == "preserved"

    # Source image unchanged
    assert list(sdata2.images["stitched_image"]["scale0"]["image"].coords["c"].values) == [
        "DNA",
        "Membrane",
        "PanCK",
    ]


def test_merge_channels_single_channel_noop():
    arr = np.full((1, 4, 4), 100, dtype=np.uint16)
    da = xr.DataArray(arr, dims=["c", "y", "x"])
    im = Image2DModel.parse(da, c_coords=["a"], transformations={"global": Identity()})
    sdata = SpatialData(images={"im": im})

    ctx = {"args": {"image_key": "im", "channels": ["a"]}, "stage": "before_image_segmentation"}
    MergeChannelsOperation().validate(ctx, sdata)
    sdata2, _ = MergeChannelsOperation().apply(sdata, ctx)

    assert list(sdata2.images["im"].coords["c"].values) == ["a"]


def test_filter_cells_backup_and_predicate():
    sdata = SpatialData(shapes={"cellpose_boundaries": _shapes()})
    orig = sdata.shapes["cellpose_boundaries"]
    ctx = {
        "args": {"filters": [{"column": "area", "min": 3}]},
        "stage": "after_cellpose",
    }
    op = FilterCellsOperation()
    op.validate(ctx, sdata)
    sdata2, report = op.apply(sdata, ctx)

    assert "cellpose_boundaries_unfiltered" in sdata2.shapes
    backup = sdata2.shapes["cellpose_boundaries_unfiltered"]
    assert len(backup) == len(orig)
    assert list(backup.index) == list(orig.index)

    assert report["original_count"] == 3
    assert report["retained_count"] < 3
    assert report["removed_count"] > 0


def test_filter_cells_rejects_existing_backup():
    sdata = SpatialData(
        shapes={
            "cellpose_boundaries": _shapes(),
            "cellpose_boundaries_unfiltered": _shapes(),
        }
    )
    ctx = {"args": {"filters": [{"column": "area", "min": 3}]}, "stage": "after_cellpose"}
    with pytest.raises(OperationError):
        FilterCellsOperation().validate(ctx, sdata)


def test_filter_cells_rejects_all_removed():
    sdata = SpatialData(shapes={"cellpose_boundaries": _shapes()})
    ctx = {"args": {"filters": [{"column": "area", "min": 100}]}, "stage": "after_cellpose"}
    FilterCellsOperation().validate(ctx, sdata)
    with pytest.raises(OperationError):
        FilterCellsOperation().apply(sdata, ctx)
