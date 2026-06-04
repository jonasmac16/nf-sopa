#!/usr/bin/env python3
from __future__ import annotations

import sys
import types
from enum import Enum
from typing import Iterable

import numpy as np
import typer
import xarray as xr
from spatialdata import SpatialData
from spatialdata.transformations import set_transformation
from xarray import DataArray


class CombineMethod(str, Enum):
    MAX = "max"
    PROD = "prod"


def _as_list(channels: str | Iterable[str], role: str) -> list[str]:
    if isinstance(channels, str):
        channels = [channels]
    else:
        channels = list(channels)

    assert channels, f"At least one {role} channel must be provided."
    return channels


def _validate_channels(image: DataArray, channels: list[str], role: str):
    available = list(map(str, image.coords["c"].values))
    missing = [channel for channel in channels if channel not in available]

    assert not missing, f"Unknown {role} channel(s): {missing}. Available channels are: {available}"


def _combine_multiple_channels(
    image: DataArray,
    channels: list[str],
    combined_name: str,
    method: CombineMethod,
) -> DataArray:
    selected = image.sel(c=channels)

    if len(channels) == 1:
        return selected.assign_coords(c=[combined_name])

    if method == CombineMethod.MAX:
        combined = selected.max(dim="c")
    elif method == CombineMethod.PROD:
        if np.issubdtype(selected.dtype, np.integer):
            promoted = selected.astype(np.uint64)
            combined = promoted.prod(dim="c")
            info = np.iinfo(image.dtype)
            combined = combined.clip(min=0, max=info.max).astype(image.dtype)
        else:
            combined = selected.astype(np.float32).prod(dim="c").astype(np.float32)
    else:
        raise ValueError(f"Unknown method: {method}")

    return combined.expand_dims(c=[combined_name])


def build_segmentation_channels_image(
    sdata: SpatialData,
    nuclear_channels: str | Iterable[str],
    membrane_channels: str | Iterable[str],
    image_key: str | None = None,
    nuclear_method: CombineMethod = CombineMethod.MAX,
    membrane_method: CombineMethod = CombineMethod.MAX,
    nuclear_name: str = "nuclear",
    membrane_name: str = "membrane",
) -> DataArray:
    from sopa.utils import copy_transformations, get_spatial_image

    image = get_spatial_image(sdata, key=image_key)
    nuclear_channels = _as_list(nuclear_channels, "nuclear")
    membrane_channels = _as_list(membrane_channels, "membrane")

    _validate_channels(image, nuclear_channels, "nuclear")
    _validate_channels(image, membrane_channels, "membrane")

    nuclear = _combine_multiple_channels(image, nuclear_channels, nuclear_name, nuclear_method)
    membrane = _combine_multiple_channels(image, membrane_channels, membrane_name, membrane_method)

    combined = xr.concat([nuclear, membrane], dim="c").transpose("c", "y", "x")
    combined.name = f"{image.name or 'image'}_segmentation_channels"
    set_transformation(combined, copy_transformations(image), set_all=True)
    return combined


def add_segmentation_channels(
    sdata: SpatialData,
    nuclear_channels: str | Iterable[str],
    membrane_channels: str | Iterable[str],
    image_key: str | None = None,
    nuclear_method: CombineMethod = CombineMethod.MAX,
    membrane_method: CombineMethod = CombineMethod.MAX,
    key_added: str = "segmentation_channels",
    set_as_cell_segmentation_image: bool = False,
):
    from sopa.constants import SopaAttrs
    from sopa.utils import add_spatial_element

    combined = build_segmentation_channels_image(
        sdata=sdata,
        nuclear_channels=nuclear_channels,
        membrane_channels=membrane_channels,
        image_key=image_key,
        nuclear_method=nuclear_method,
        membrane_method=membrane_method,
    )

    add_spatial_element(sdata, key_added, combined, overwrite=True)

    if set_as_cell_segmentation_image:
        sdata.attrs[SopaAttrs.CELL_SEGMENTATION] = key_added
        if sdata.is_backed():
            sdata.write_attrs()


def _install_python_api_patch():
    import sopa.segmentation as segmentation

    segmentation.CombineMethod = CombineMethod
    segmentation.build_segmentation_channels_image = build_segmentation_channels_image
    segmentation.add_segmentation_channels = add_segmentation_channels

    channels_module = types.ModuleType("sopa.segmentation.channels")
    channels_module.CombineMethod = CombineMethod
    channels_module.build_segmentation_channels_image = build_segmentation_channels_image
    channels_module.add_segmentation_channels = add_segmentation_channels
    sys.modules["sopa.segmentation.channels"] = channels_module


def _install_cli_patch():
    from sopa.cli.segmentation import SDATA_HELPER, app_segmentation

    existing = {command.name for command in app_segmentation.registered_commands}
    if "combine-channels" in existing:
        return

    @app_segmentation.command("combine-channels")
    def combine_channels(
        sdata_path: str = typer.Argument(help=SDATA_HELPER),
        nuclear_channel: list[str] = typer.Option(
            ...,
            help="Name(s) of nuclear channel(s). Repeat option for multiple channels.",
        ),
        membrane_channel: list[str] = typer.Option(
            ...,
            help="Name(s) of membrane channel(s). Repeat option for multiple channels.",
        ),
        image_key: str | None = typer.Option(
            None,
            help="Optional image key in sdata.images.",
        ),
        nuclear_method: CombineMethod = typer.Option(
            CombineMethod.MAX,
            help="Nuclear combine method: max or prod.",
        ),
        membrane_method: CombineMethod = typer.Option(
            CombineMethod.MAX,
            help="Membrane combine method: max or prod.",
        ),
        key_added: str = typer.Option(
            "segmentation_channels",
            help="Output image key to add in sdata.images.",
        ),
        set_as_segmentation_image: bool = typer.Option(
            False,
            help="Set as sdata.attrs['cell_segmentation_image'].",
        ),
    ):
        from sopa.io.standardize import read_zarr_standardized

        sdata = read_zarr_standardized(sdata_path)
        add_segmentation_channels(
            sdata=sdata,
            nuclear_channels=nuclear_channel,
            membrane_channels=membrane_channel,
            image_key=image_key,
            nuclear_method=nuclear_method,
            membrane_method=membrane_method,
            key_added=key_added,
            set_as_cell_segmentation_image=set_as_segmentation_image,
        )


def install_patch(with_cli: bool = True):
    _install_python_api_patch()
    if with_cli:
        _install_cli_patch()


if __name__ == "__main__":
    install_patch(with_cli=True)
    from sopa.cli.app import app

    app()
