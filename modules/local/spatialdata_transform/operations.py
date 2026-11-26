"""Registry and operations for the generic SpatialData transformation framework."""

from __future__ import annotations

import json
from typing import Any

import dask.array as da
import numpy as np
import xarray as xr
from dask.base import is_dask_collection
from geopandas import GeoDataFrame
from scipy import ndimage
from skimage.morphology import disk, square, white_tophat
from skimage.restoration import rolling_ball
from spatialdata import SpatialData
from spatialdata.models import Image2DModel, ShapesModel, TableModel
from spatialdata.transformations import get_transformation


class OperationError(Exception):
    """Raised when an operation fails validation or execution."""


class Operation:
    """Base class for all SpatialData transformation operations.

    Subclasses must set ``name`` and implement ``apply``. They may override
    ``validate`` to perform operation-specific argument and element validation.
    """

    name: str = ""
    supported_stages: list[str] = []
    affected_element_types: list[str] = []

    def validate(self, context: dict[str, Any], sdata: SpatialData) -> None:
        """Validate the operation for the given context and SpatialData object.

        Raises:
            OperationError: if validation fails.
        """
        stage = context.get("stage")
        if self.supported_stages and stage not in self.supported_stages:
            raise OperationError(
                f"Operation '{self.name}' does not support stage '{stage}'. "
                f"Supported stages: {', '.join(self.supported_stages)}."
            )

    def apply(self, sdata: SpatialData, context: dict[str, Any]) -> tuple[SpatialData, dict[str, Any]]:
        """Apply the operation and return the updated SpatialData object and a report."""
        raise NotImplementedError


class NoopOperation(Operation):
    """Identity operation. Useful for testing framework wiring."""

    name = "noop"
    supported_stages = []
    affected_element_types = []

    def apply(self, sdata: SpatialData, context: dict[str, Any]) -> tuple[SpatialData, dict[str, Any]]:
        return sdata, {"message": "no operation performed"}


class AssertElementOperation(Operation):
    """Validate that a SpatialData element exists.

    This operation does not modify the object; it is intended for stage-wiring
    tests and for defensive checks inside user-defined operation chains.
    """

    name = "assert_element"
    supported_stages = []
    affected_element_types = ["images", "shapes", "points", "tables"]

    def validate(self, context: dict[str, Any], sdata: SpatialData) -> None:
        super().validate(context, sdata)
        args = context.get("args", {})
        element_type = args.get("element_type")
        element_key = args.get("element_key")

        if element_type not in self.affected_element_types:
            raise OperationError(
                f"assert_element requires element_type in {self.affected_element_types}, got '{element_type}'."
            )
        if not isinstance(element_key, str) or not element_key:
            raise OperationError("assert_element requires a non-empty string element_key.")

        collection = getattr(sdata, element_type)
        if element_key not in collection:
            raise OperationError(
                f"Missing required {element_type} element '{element_key}'. Available: {list(collection.keys())}."
            )

    def apply(self, sdata: SpatialData, context: dict[str, Any]) -> tuple[SpatialData, dict[str, Any]]:
        args = context.get("args", {})
        return sdata, {
            "element_type": args["element_type"],
            "element_key": args["element_key"],
            "found": True,
        }


class AddTestShapesOperation(Operation):
    """Add a minimal shapes element with one dummy polygon.

    This is a test-only operation that mutates the SpatialData object in a
    detectable but non-destructive way, allowing tests to verify that a
    transform output is consumed by downstream modules.
    """

    name = "add_test_shapes"
    supported_stages = []
    affected_element_types = ["shapes"]

    def validate(self, context: dict[str, Any], sdata: SpatialData) -> None:
        super().validate(context, sdata)
        args = context.get("args", {})
        shapes_key = args.get("shapes_key")
        if not isinstance(shapes_key, str) or not shapes_key:
            raise OperationError("add_test_shapes requires a non-empty string shapes_key.")
        if shapes_key in sdata.shapes:
            raise OperationError(f"Shapes key '{shapes_key}' already exists.")

    def apply(self, sdata: SpatialData, context: dict[str, Any]) -> tuple[SpatialData, dict[str, Any]]:
        args = context.get("args", {})
        shapes_key = args["shapes_key"]
        from shapely.geometry import Polygon

        gdf = GeoDataFrame({"geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]})
        sdata.shapes[shapes_key] = ShapesModel.parse(gdf)
        return sdata, {"shapes_key": shapes_key}


# ---------------------------------------------------------------------------
# Specific SpatialData operations introduced in Part 2.
# ---------------------------------------------------------------------------


def _require_arg(args: dict[str, Any], name: str, types: tuple[type, ...] | type) -> Any:
    """Return an argument or raise a diagnostic OperationError."""
    if name not in args:
        raise OperationError(f"Missing required argument '{name}'.")
    value = args[name]
    if not isinstance(value, types):
        raise OperationError(f"Argument '{name}' must be a {types}, got {type(value).__name__}.")
    return value


# ---- image helpers ---------------------------------------------------------


_UINT16_MAX = int(np.iinfo(np.uint16).max)
_UINT16_SCALE = (_UINT16_MAX - 1) / _UINT16_MAX


def _is_multiscale_image(image: xr.DataArray | Any) -> bool:
    """Return True if the image element is a multiscale (DataTree) image."""
    return hasattr(image, "children") and hasattr(image, "groups")


def _get_scale_arrays(image: Any) -> list[tuple[str, xr.DataArray]]:
    """Yield (scale_name, image_dataarray) pairs for a SpatialData image."""
    if isinstance(image, xr.DataArray):
        return [("image", image)]

    if _is_multiscale_image(image):
        result: list[tuple[str, xr.DataArray]] = []
        for scale_name in image.keys():
            node = image[scale_name]
            if "image" not in node:
                raise OperationError(f"Multiscale node '{scale_name}' has no 'image' data variable.")
            result.append((scale_name, node["image"]))
        return result

    raise OperationError(f"Unsupported image type: {type(image).__name__}.")


def _set_scale_array(image: Any, scale_name: str, new_da: xr.DataArray) -> None:
    """Assign a corrected DataArray back to the image element."""
    if isinstance(image, xr.DataArray):
        return

    image[scale_name]["image"] = new_da


def _image_element_after_update(
    sdata: SpatialData,
    image_key: str,
    updated_image: xr.DataArray | Any,
) -> None:
    """Replace an image element while keeping its SpatialData key."""
    sdata.images[image_key] = updated_image


def _channel_dataarray(da: xr.DataArray, channel: Any) -> xr.DataArray:
    """Select a single channel and verify that the selection is unambiguous."""
    if "c" not in da.dims:
        raise OperationError(f"Image has no channel dimension ('c'); dims are {list(da.dims)}.")

    c_coord = da.coords.get("c")
    if c_coord is None:
        raise OperationError("Image channel dimension has no coordinate labels.")

    available = list(c_coord.values)
    if channel not in available:
        raise OperationError(
            f"Channel '{channel}' not found in image. Available channels: {available}."
        )

    if list(available).count(channel) > 1:
        raise OperationError(f"Channel label '{channel}' is ambiguous (duplicated in coordinate).")

    return da.sel(c=channel)


def _summary_stats(array: xr.DataArray) -> dict[str, Any]:
    """Compute lightweight summary statistics for a single channel/array."""
    try:
        min_val = float(array.min())
        max_val = float(array.max())
        mean_val = float(array.mean())
    except Exception:
        min_val = max_val = mean_val = None
    return {"min": min_val, "max": max_val, "mean": mean_val}


def _clip_cast(array: xr.DataArray, dtype: np.dtype[Any]) -> xr.DataArray:
    """Clip to the target dtype range and cast without wraparound."""
    if np.issubdtype(dtype, np.integer):
        info = np.iinfo(dtype)
        clipped = array.clip(info.min, info.max)
    elif np.issubdtype(dtype, np.floating):
        clipped = array
    else:
        raise OperationError(f"Unsupported target dtype for background correction: {dtype}.")
    return clipped.astype(dtype)


def _apply_dask_or_numpy(
    arr: np.ndarray | da.Array,
    func: Any,
    depth: int | dict[int, int] = 0,
    **kwargs: Any,
) -> np.ndarray | da.Array:
    """Apply ``func`` lazily with map_overlap for dask arrays, or directly for numpy."""
    if is_dask_collection(arr):
        if depth:
            return arr.map_overlap(func, depth=depth, boundary="reflect", trim=True, **kwargs)
        return arr.map_blocks(func, **kwargs)
    return func(arr, **kwargs)


def _background_correct_channel(
    channel_da: xr.DataArray,
    method: str,
    kwargs: dict[str, Any],
) -> xr.DataArray:
    """Apply a background-correction method to a single-channel DataArray.

    The returned DataArray preserves the input channel's dimensions, coordinates,
    and attributes, and has the same dtype as the input.
    """
    in_dtype = channel_da.dtype
    if not np.issubdtype(in_dtype, np.number):
        raise OperationError(f"Background correction requires numeric data, got dtype {in_dtype}.")

    data = channel_da.data

    if method == "subtract_constant":
        value = float(kwargs["value"])
        corrected = data - value

    elif method == "divide":
        value = float(kwargs["value"])
        if value == 0:
            raise OperationError("divide background correction requires a non-zero divisor.")
        corrected = data / value

    elif method == "gaussian":
        sigma = kwargs["sigma"]
        try:
            sigma = float(sigma)
            ndim = data.ndim
            sigma_tuple = (sigma,) * ndim
        except Exception as exc:
            raise OperationError(f"Invalid sigma '{sigma}' for gaussian background correction.") from exc
        if sigma <= 0:
            raise OperationError("gaussian background correction requires sigma > 0.")
        try:
            import dask_image.ndfilters as dask_ndfilters

            if is_dask_collection(data):
                background = dask_ndfilters.gaussian_filter(data, sigma=sigma_tuple)
            else:
                background = ndimage.gaussian_filter(np.asarray(data), sigma=sigma_tuple)
        except Exception as exc:
            raise OperationError(f"Failed to apply gaussian background correction: {exc}") from exc
        corrected = data - background

    elif method == "rolling_ball":
        radius = kwargs["radius"]
        if not isinstance(radius, int) or radius < 0:
            raise OperationError("rolling_ball background correction requires an integer radius >= 0.")
        depth = radius

        def _rb(block: np.ndarray, radius: int = radius) -> np.ndarray:
            return block - rolling_ball(block, radius=radius)

        corrected = _apply_dask_or_numpy(data, _rb, depth=depth)

    elif method == "tophat":
        radius = kwargs["radius"]
        selem_name = kwargs.get("selem", "disk")
        if not isinstance(radius, int) or radius < 0:
            raise OperationError("tophat background correction requires an integer radius >= 0.")
        if selem_name == "disk":
            footprint = disk(radius)
        elif selem_name == "square":
            footprint = square(2 * radius + 1)
        else:
            raise OperationError(f"Unsupported tophat structuring element '{selem_name}'; use 'disk' or 'square'.")
        depth = radius

        def _th(block: np.ndarray, footprint: np.ndarray = footprint) -> np.ndarray:
            return white_tophat(block, footprint=footprint)

        corrected = _apply_dask_or_numpy(data, _th, depth=depth)

    else:
        raise OperationError(
            f"Unknown background-correction method '{method}'. "
            f"Supported methods: subtract_constant, divide, gaussian, rolling_ball, tophat."
        )

    corrected = _clip_cast(xr.DataArray(corrected, dims=channel_da.dims, coords=channel_da.coords), in_dtype)
    corrected.attrs.update(channel_da.attrs)
    return corrected


class BackgroundCorrectionOperation(Operation):
    """Single-channel background correction for a SpatialData image.

    The operation modifies exactly one channel of one image. All other channels,
    spatial coordinates, coordinate transformations, units, scales, and multiscale
    relationships are preserved.

    Supported correction methods (chosen explicitly via ``method``):

    - ``subtract_constant``: subtract a user-provided constant from the channel.
    - ``divide``: divide the channel by a user-provided constant.
    - ``gaussian``: subtract a Gaussian-filtered background estimate (parameter ``sigma``).
    - ``rolling_ball``: subtract a rolling-ball background estimate (parameter ``radius``).
    - ``tophat``: apply a white top-hat transform (morphological background
      subtraction; parameters ``radius`` and optionally ``selem``).

    The output is clipped to the input dtype range to prevent overflow/wraparound.
    """

    name = "background_correction"
    supported_stages = ["before_image_segmentation"]
    affected_element_types = ["images"]

    _METHODS = {"subtract_constant", "divide", "gaussian", "rolling_ball", "tophat"}

    def validate(self, context: dict[str, Any], sdata: SpatialData) -> None:
        super().validate(context, sdata)
        args = context.get("args", {})

        image_key = _require_arg(args, "image_key", str)
        channel = _require_arg(args, "channel", str)
        method = _require_arg(args, "method", str)

        if method not in self._METHODS:
            raise OperationError(
                f"Unknown background-correction method '{method}'. "
                f"Supported methods: {', '.join(sorted(self._METHODS))}."
            )

        if image_key not in sdata.images:
            raise OperationError(
                f"Image '{image_key}' not found. Available images: {list(sdata.images.keys())}."
            )

        image = sdata.images[image_key]
        try:
            scale_arrays = _get_scale_arrays(image)
        except OperationError:
            raise
        except Exception as exc:
            raise OperationError(f"Could not inspect image '{image_key}': {exc}") from exc

        if not scale_arrays:
            raise OperationError(f"Image '{image_key}' contains no scale data.")

        for scale_name, da_arr in scale_arrays:
            try:
                _channel_dataarray(da_arr, channel)
            except OperationError as exc:
                raise OperationError(
                    f"Image '{image_key}' scale '{scale_name}' is missing channel '{channel}'."
                ) from exc

            if not np.issubdtype(da_arr.dtype, np.number):
                raise OperationError(
                    f"Image '{image_key}' scale '{scale_name}' has non-numeric dtype {da_arr.dtype}."
                )

        if method == "subtract_constant":
            _require_arg(args, "value", (int, float))
        elif method == "divide":
            _require_arg(args, "value", (int, float))
            if args["value"] == 0:
                raise OperationError("divide method requires a non-zero value.")
        elif method == "gaussian":
            _require_arg(args, "sigma", (int, float))
            if args["sigma"] <= 0:
                raise OperationError("gaussian method requires sigma > 0.")
        elif method == "rolling_ball":
            _require_arg(args, "radius", int)
            if args["radius"] < 0:
                raise OperationError("rolling_ball method requires radius >= 0.")
        elif method == "tophat":
            _require_arg(args, "radius", int)
            if args["radius"] < 0:
                raise OperationError("tophat method requires radius >= 0.")
            if "selem" in args and args["selem"] not in ("disk", "square"):
                raise OperationError("tophat selem must be 'disk' or 'square'.")

    def apply(self, sdata: SpatialData, context: dict[str, Any]) -> tuple[SpatialData, dict[str, Any]]:
        args = context.get("args", {})
        image_key = args["image_key"]
        channel = args["channel"]
        method = args["method"]
        method_kwargs = {k: v for k, v in args.items() if k not in ("image_key", "channel", "method")}

        image = sdata.images[image_key]
        scale_arrays = _get_scale_arrays(image)

        before_stats: dict[str, Any] = {}
        after_stats: dict[str, Any] = {}

        for scale_name, da_arr in scale_arrays:
            channel_da = _channel_dataarray(da_arr, channel)
            before_stats[scale_name] = _summary_stats(channel_da)

            corrected_channel = _background_correct_channel(channel_da, method, method_kwargs)

            updated_da = da_arr.copy()
            updated_da.loc[dict(c=channel)] = corrected_channel

            if isinstance(image, xr.DataArray):
                image = updated_da
            else:
                _set_scale_array(image, scale_name, updated_da)

            after_stats[scale_name] = _summary_stats(updated_da.sel(c=channel))

        _image_element_after_update(sdata, image_key, image)

        return sdata, {
            "image_key": image_key,
            "channel": channel,
            "method": method,
            "method_args": method_kwargs,
            "input_dtype": str(scale_arrays[0][1].dtype),
            "output_dtype": str(scale_arrays[0][1].dtype),
            "before_stats": before_stats,
            "after_stats": after_stats,
        }


# ---- merge channels --------------------------------------------------------


_SOPA_CELL_SEGMENTATION_ATTR = "cell_segmentation_image"


def _to_uint16(array: xr.DataArray) -> xr.DataArray:
    """Convert an array to uint16 using the WEHI SODA Hub reference scaling rule."""
    max_value = float(array.max())
    if max_value > _UINT16_MAX:
        scaled = (array * _UINT16_SCALE).clip(0, _UINT16_MAX)
        return scaled.astype(np.uint16)
    return array.astype(np.uint16)


def _get_image_scale_factors(image: Any) -> list[int] | None:
    """Infer the Image2DModel scale factors from an existing multiscale image."""
    if not _is_multiscale_image(image):
        return None

    scale_names = sorted(image.keys(), key=lambda name: int(name.replace("scale", "")))
    factors: list[int] = []
    for prev_name, next_name in zip(scale_names[:-1], scale_names[1:]):
        prev_da = image[prev_name]["image"]
        next_da = image[next_name]["image"]
        factor_y = prev_da.sizes["y"] // next_da.sizes["y"]
        factor_x = prev_da.sizes["x"] // next_da.sizes["x"]
        if factor_y != factor_x:
            raise OperationError(
                f"Non-square scale factor between '{prev_name}' and '{next_name}': {factor_y}x{factor_x}."
            )
        factors.append(factor_y)
    return factors


def _get_image_transformations(image: Any) -> dict[str, Any] | None:
    """Return the coordinate transformations attached to a SpatialData image element."""
    try:
        return get_transformation(image, get_all=True)
    except Exception:
        return None


def _merge_channel_group(
    da: xr.DataArray,
    source_channels: list[str],
    output_channel: str,
    method: str,
) -> xr.DataArray:
    """Create one output channel from one or more source channels.

    Single-source channels are copied exactly (with the output channel label).
    Multi-source channels are merged with the selected method.
    """
    if len(source_channels) == 1:
        merged = da.sel(c=source_channels[0])
    else:
        selected = da.sel(c=source_channels)
        if method == "max":
            merged = selected.max(dim="c")
        elif method == "prod":
            merged = selected.astype(np.uint64).prod(dim="c")
            merged = _to_uint16(merged)
        else:
            raise OperationError(f"Unknown merge_channels method '{method}'; use 'max' or 'prod'.")

    return merged.expand_dims(c=[output_channel])


def _merge_channels_single_scale(
    da: xr.DataArray,
    channels: list[str],
    output_channel: str,
    method: str,
) -> xr.DataArray:
    """Append a combined channel to a single-scale image DataArray (legacy mode)."""
    if len(channels) == 1:
        return da

    selected = da.sel(c=channels)

    if method == "max":
        combined = selected.max(dim="c")
    elif method == "prod":
        combined = selected.astype(np.uint64).prod(dim="c")
    else:
        raise OperationError(f"Unknown merge_channels method '{method}'; use 'max' or 'prod'.")

    combined_uint16 = _to_uint16(combined)
    combined_da = combined_uint16.expand_dims(c=[output_channel])

    new_da = xr.concat([da, combined_da], dim="c")
    new_da.attrs.update(da.attrs)
    new_da.name = da.name
    return new_da


class MergeChannelsOperation(Operation):
    """Combine selected image channels into an additional channel or a new image.

    Two modes are supported:

    1. Legacy append mode (default): merge one group of channels and append the
       result to the source image. The source image is modified in place.
    2. Segmentation-image mode: create a separate multiscale image containing
       one or more channel groups. The source image is left unchanged, and the
       new image is registered as the cell segmentation image.

    The channel-group syntax is a mapping from output channel name to an ordered
    list of source channels. Single-source groups are copied exactly;
    multi-source groups are merged with the selected method.

    Supported methods:

    - ``max``: pixel-wise maximum over the selected channels.
    - ``prod``: pixel-wise product over the selected channels, computed in
      ``uint64`` and converted back to ``uint16`` with the reference scaling
      rule.
    """

    name = "merge_channels"
    supported_stages = ["before_image_segmentation"]
    affected_element_types = ["images"]

    def validate(self, context: dict[str, Any], sdata: SpatialData) -> None:
        super().validate(context, sdata)
        args = context.get("args", {})

        image_key = _require_arg(args, "image_key", str)
        output_image_key = args.get("output_image_key")
        channel_groups = args.get("channel_groups")
        channels = args.get("channels")
        output_channel = args.get("output_channel", "combined_membrane")
        method = args.get("method", "max")

        if output_image_key is not None:
            if not isinstance(output_image_key, str) or not output_image_key:
                raise OperationError("output_image_key must be a non-empty string.")
            if image_key == output_image_key:
                raise OperationError("output_image_key must differ from image_key.")
            if output_image_key in sdata.images:
                raise OperationError(f"Image '{output_image_key}' already exists.")

            channel_groups = _require_arg(args, "channel_groups", dict)
            if not channel_groups:
                raise OperationError("channel_groups must contain at least one group.")
            for output_ch, source_channels in channel_groups.items():
                if not isinstance(output_ch, str) or not output_ch:
                    raise OperationError("All channel_groups keys must be non-empty strings.")
                if not isinstance(source_channels, list) or not source_channels:
                    raise OperationError(f"Channel group '{output_ch}' must contain at least one source channel.")
                if not all(isinstance(ch, str) and ch for ch in source_channels):
                    raise OperationError(f"All source channels in group '{output_ch}' must be non-empty strings.")
                if len(source_channels) != len(set(source_channels)):
                    raise OperationError(f"Duplicate source channels in group '{output_ch}': {source_channels}.")

        elif channels is not None:
            if not isinstance(channels, list) or not channels:
                raise OperationError("merge_channels requires at least one channel.")
            if not all(isinstance(ch, str) and ch for ch in channels):
                raise OperationError("All entries in 'channels' must be non-empty strings.")
            if len(channels) != len(set(channels)):
                raise OperationError(f"Duplicate channel selections are not allowed: {channels}.")
            if not isinstance(output_channel, str) or not output_channel:
                raise OperationError("output_channel must be a non-empty string.")

        else:
            raise OperationError("Provide either 'channels' (legacy mode) or 'channel_groups' (segmentation-image mode).")

        if method not in ("max", "prod"):
            raise OperationError(f"merge_channels method must be 'max' or 'prod', got '{method}'.")

        if image_key not in sdata.images:
            raise OperationError(
                f"Image '{image_key}' not found. Available images: {list(sdata.images.keys())}."
            )

        image = sdata.images[image_key]
        scale_arrays = _get_scale_arrays(image)

        source_channels_to_check = (
            [ch for group in channel_groups.values() for ch in group]
            if channel_groups is not None
            else channels
        )

        for scale_name, da_arr in scale_arrays:
            if "c" not in da_arr.dims:
                raise OperationError(
                    f"Image '{image_key}' scale '{scale_name}' has no channel dimension."
                )
            available = list(da_arr.coords.get("c", []).values)
            missing = [ch for ch in source_channels_to_check if ch not in available]
            if missing:
                raise OperationError(
                    f"Scale '{scale_name}' is missing channels {missing}. Available: {available}."
                )

        if channel_groups is None:
            for scale_name, da_arr in scale_arrays:
                available = list(da_arr.coords.get("c", []).values)
                if output_channel in available:
                    raise OperationError(
                        f"Output channel '{output_channel}' already exists in image '{image_key}' scale '{scale_name}'."
                    )

    def apply(self, sdata: SpatialData, context: dict[str, Any]) -> tuple[SpatialData, dict[str, Any]]:
        args = context.get("args", {})
        image_key = args["image_key"]
        output_image_key = args.get("output_image_key")
        channel_groups = args.get("channel_groups")
        method = args.get("method", "max")

        image = sdata.images[image_key]

        if output_image_key is not None:
            return self._apply_segmentation_image(
                sdata, image_key, output_image_key, channel_groups, method
            )

        channels = list(args["channels"])
        output_channel = args.get("output_channel", "combined_membrane")
        scale_arrays = _get_scale_arrays(image)

        for scale_name, da_arr in scale_arrays:
            merged = _merge_channels_single_scale(da_arr, channels, output_channel, method)
            if isinstance(image, xr.DataArray):
                image = merged
            else:
                _set_scale_array(image, scale_name, merged)

        _image_element_after_update(sdata, image_key, image)

        return sdata, {
            "image_key": image_key,
            "channels": channels,
            "output_channel": output_channel,
            "method": method,
            "input_dtype": str(scale_arrays[0][1].dtype),
            "output_channels": list(image.coords["c"].values)
            if isinstance(image, xr.DataArray)
            else list(image["scale0"]["image"].coords["c"].values),
        }

    def _apply_segmentation_image(
        self,
        sdata: SpatialData,
        image_key: str,
        output_image_key: str,
        channel_groups: dict[str, list[str]],
        method: str,
    ) -> tuple[SpatialData, dict[str, Any]]:
        image = sdata.images[image_key]
        scale_arrays = _get_scale_arrays(image)
        scale0_da = scale_arrays[0][1]

        merged_channels: list[xr.DataArray] = []
        for output_ch, source_channels in channel_groups.items():
            merged_channels.append(_merge_channel_group(scale0_da, source_channels, output_ch, method))

        merged_da = xr.concat(merged_channels, dim="c")
        merged_da.attrs.update({k: v for k, v in scale0_da.attrs.items() if k != "transform"})
        merged_da.attrs.pop("transform", None)
        merged_da.name = scale0_da.name

        scale_factors = _get_image_scale_factors(image)
        transformations = _get_image_transformations(image)

        new_image = Image2DModel.parse(
            merged_da,
            c_coords=list(merged_da.coords["c"].values),
            scale_factors=scale_factors,
            transformations=transformations,
        )

        sdata.images[output_image_key] = new_image
        sdata.attrs[_SOPA_CELL_SEGMENTATION_ATTR] = output_image_key

        return sdata, {
            "image_key": image_key,
            "output_image_key": output_image_key,
            "channel_groups": channel_groups,
            "method": method,
            "input_dtype": str(scale0_da.dtype),
            "output_channels": list(new_image["scale0"]["image"].coords["c"].values)
            if _is_multiscale_image(new_image)
            else list(new_image.coords["c"].values),
        }


# ---- filter cells ----------------------------------------------------------


_GEOMETRY_DERIVED_COLUMNS: dict[str, Any] = {
    "area": lambda gdf: gdf.geometry.area,
    "perimeter": lambda gdf: gdf.geometry.length,
    "bounds_minx": lambda gdf: gdf.geometry.bounds["minx"],
    "bounds_miny": lambda gdf: gdf.geometry.bounds["miny"],
    "bounds_maxx": lambda gdf: gdf.geometry.bounds["maxx"],
    "bounds_maxy": lambda gdf: gdf.geometry.bounds["maxy"],
}


def _get_filter_column(gdf: GeoDataFrame, column: str) -> Any:
    """Return a pandas Series for a named column or a geometry-derived property."""
    if column in gdf.columns:
        return gdf[column]
    if column in _GEOMETRY_DERIVED_COLUMNS:
        return _GEOMETRY_DERIVED_COLUMNS[column](gdf)
    raise OperationError(
        f"Filter column '{column}' not found in shapes table. "
        f"Available columns: {list(gdf.columns)}; geometry properties: {list(_GEOMETRY_DERIVED_COLUMNS)}."
    )


def _evaluate_filters(gdf: GeoDataFrame, filters: list[dict[str, Any]]) -> Any:
    """Return a boolean mask for rows matching all configured predicates."""
    mask = np.ones(len(gdf), dtype=bool)
    for predicate in filters:
        column = _require_arg(predicate, "column", str)
        series = _get_filter_column(gdf, column)

        if not np.issubdtype(series.dtype, np.number):
            raise OperationError(
                f"Filter column '{column}' has non-numeric dtype '{series.dtype}'."
            )

        null_mask = series.isna()
        keep_nulls = bool(predicate.get("keep_nulls", False))
        col_mask = ~null_mask if not keep_nulls else np.ones(len(gdf), dtype=bool)

        if "min" in predicate and predicate["min"] is not None:
            col_mask &= series >= predicate["min"]
        if "max" in predicate and predicate["max"] is not None:
            col_mask &= series <= predicate["max"]

        if keep_nulls:
            col_mask |= null_mask

        mask &= col_mask

    return mask


class FilterCellsOperation(Operation):
    """Filter shapes (e.g. Cellpose boundaries) using declarative numeric predicates.

    Before filtering, the complete source shapes element is copied to a backup
    element. The filtered shapes are written back to the original key so that
    downstream transcript-based segmentation uses the filtered prior. The backup
    is never used as a downstream prior unless explicitly configured elsewhere.

    Predicates are configured as a list of ``{"column": "...", "min": ..., "max": ...}``
    maps. ``column`` may be any numeric column in the GeoDataFrame or one of the
    geometry-derived properties ``area``, ``perimeter``, ``bounds_minx``,
    ``bounds_miny``, ``bounds_maxx``, ``bounds_maxy``. Filtering that would
    remove every shape is rejected to avoid producing an invalid empty shapes
    element.
    """

    name = "filter_cells"
    supported_stages = ["after_cellpose", "after_stardist"]
    affected_element_types = ["shapes"]

    def validate(self, context: dict[str, Any], sdata: SpatialData) -> None:
        super().validate(context, sdata)
        args = context.get("args", {})

        source = args.get("source", "cellpose_boundaries")
        backup_key = args.get("backup_key", "cellpose_boundaries_unfiltered")
        filters = _require_arg(args, "filters", list)

        if not isinstance(source, str) or not source:
            raise OperationError("source must be a non-empty string.")
        if not isinstance(backup_key, str) or not backup_key:
            raise OperationError("backup_key must be a non-empty string.")
        if source == backup_key:
            raise OperationError("source and backup_key must be different.")

        if source not in sdata.shapes:
            raise OperationError(
                f"Source shapes '{source}' not found. Available shapes: {list(sdata.shapes.keys())}."
            )
        if backup_key in sdata.shapes:
            raise OperationError(
                f"Backup shapes key '{backup_key}' already exists. "
                "Refusing to overwrite an existing unfiltered backup."
            )

        if not filters:
            raise OperationError("At least one filter predicate is required.")

        gdf = sdata.shapes[source]
        for index, predicate in enumerate(filters):
            if not isinstance(predicate, dict):
                raise OperationError(f"Filter predicate #{index} must be a map.")
            column = _require_arg(predicate, "column", str)
            _ = _get_filter_column(gdf, column)  # validate existence and numeric dtype

            for bound in ("min", "max"):
                if bound in predicate and predicate[bound] is not None:
                    if not isinstance(predicate[bound], (int, float)):
                        raise OperationError(
                            f"Filter predicate #{index} '{bound}' must be numeric or null."
                        )

        # Reject configurations where a table is linked to the source shapes,
        # because we do not silently leave stale instance references.
        for table_name, table in sdata.tables.items():
            regions = table.uns.get(TableModel.ATTRS_KEY, {}).get("region") if hasattr(table, "uns") else None
            if isinstance(regions, str):
                regions = [regions]
            if regions and source in regions:
                raise OperationError(
                    f"A table ('{table_name}') is linked to source shapes '{source}'. "
                    "Filtering linked shapes without updating the table would leave stale references."
                )

    def apply(self, sdata: SpatialData, context: dict[str, Any]) -> tuple[SpatialData, dict[str, Any]]:
        args = context.get("args", {})
        source = args.get("source", "cellpose_boundaries")
        backup_key = args.get("backup_key", "cellpose_boundaries_unfiltered")
        filters = list(args.get("filters", []))

        source_gdf = sdata.shapes[source]
        original_count = len(source_gdf)

        # Deep copy for the unfiltered backup, preserving index/transforms/attrs.
        backup_gdf = source_gdf.copy()
        sdata.shapes[backup_key] = ShapesModel.parse(backup_gdf)

        mask = _evaluate_filters(source_gdf, filters)
        filtered_gdf = source_gdf.loc[mask].copy()
        retained_count = len(filtered_gdf)
        removed_count = original_count - retained_count

        if retained_count == 0:
            raise OperationError(
                f"filter_cells removed all {original_count} cells from '{source}'. "
                "Refusing to create an empty shapes element."
            )

        sdata.shapes[source] = ShapesModel.parse(filtered_gdf)

        return sdata, {
            "source": source,
            "backup_key": backup_key,
            "filters": filters,
            "original_count": original_count,
            "retained_count": retained_count,
            "removed_count": removed_count,
        }


REGISTRY: dict[str, type[Operation]] = {
    NoopOperation.name: NoopOperation,
    AssertElementOperation.name: AssertElementOperation,
    AddTestShapesOperation.name: AddTestShapesOperation,
    BackgroundCorrectionOperation.name: BackgroundCorrectionOperation,
    MergeChannelsOperation.name: MergeChannelsOperation,
    FilterCellsOperation.name: FilterCellsOperation,
}


def get_operation(name: str) -> type[Operation]:
    """Resolve an operation by name.

    Raises:
        OperationError: if the operation is not registered.
    """
    try:
        return REGISTRY[name]
    except KeyError as exc:
        raise OperationError(f"Unknown operation '{name}'. Known operations: {', '.join(REGISTRY)}.") from exc


def list_operations() -> list[str]:
    """Return the names of all registered operations."""
    return list(REGISTRY.keys())
