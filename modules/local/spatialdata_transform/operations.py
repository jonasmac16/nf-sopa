"""Registry and built-in operations for the generic SpatialData transformation framework."""

from __future__ import annotations

import json
from typing import Any

from geopandas import GeoDataFrame
from spatialdata import SpatialData
from spatialdata.models import ShapesModel


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


REGISTRY: dict[str, type[Operation]] = {
    NoopOperation.name: NoopOperation,
    AssertElementOperation.name: AssertElementOperation,
    AddTestShapesOperation.name: AddTestShapesOperation,
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
