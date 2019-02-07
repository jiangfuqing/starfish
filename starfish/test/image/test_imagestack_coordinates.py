from typing import Mapping, Tuple, Union

import numpy as np
from slicedimage import ImageFormat

from starfish.experiment.builder import FetchedTile, tile_fetcher_factory
from starfish.imagestack.imagestack import ImageStack
from starfish.types import Axes, Coordinates, Number
from .imagestack_test_utils import verify_physical_coordinates

NUM_ROUND = 8
NUM_CH = 1
NUM_Z = 1
HEIGHT = 10
WIDTH = 10


def round_to_x() -> Tuple[float, float]:
    return 1000, 100


def round_to_y() -> Tuple[float, float]:
    return 10, 0.1


def round_to_z(r: int) -> Tuple[float, float]:
    return (r + 1) * 0.01, (r + 1) * 0.001


class OffsettedTiles(FetchedTile):
    """Tiles that are physically offset based on round."""
    def __init__(self, fov: int, _round: int, ch: int, z: int) -> None:
        super().__init__()
        self._round = _round

    @property
    def shape(self) -> Tuple[int, ...]:
        return HEIGHT, WIDTH

    @property
    def coordinates(self) -> Mapping[Union[str, Coordinates], Union[Number, Tuple[Number, Number]]]:
        return {
            Coordinates.X: round_to_x(),
            Coordinates.Y: round_to_y(),
            Coordinates.Z: round_to_z(self._round),
        }

    @property
    def format(self) -> ImageFormat:
        return ImageFormat.TIFF

    def tile_data(self) -> np.ndarray:
        return np.ones((HEIGHT, WIDTH), dtype=np.float32)


def test_coordinates():
    """Set up an ImageStack with tiles that are offset based on round.  Verify that the coordinates
    retrieved match.
    """
    stack = ImageStack.synthetic_stack(
        NUM_ROUND, NUM_CH, NUM_Z,
        HEIGHT, WIDTH,
        tile_fetcher=tile_fetcher_factory(
            OffsettedTiles,
            True,
        )
    )

    for selectors in stack._iter_axes({Axes.ROUND, Axes.CH, Axes.ZPLANE}):
        verify_physical_coordinates(
            stack,
            selectors,
            round_to_x(),
            round_to_y(),
            round_to_z(selectors[Axes.ROUND]),
        )


class ScalarTiles(FetchedTile):
    """Tiles that have a single scalar coordinate."""
    def __init__(self, fov: int, _round: int, ch: int, z: int) -> None:
        super().__init__()
        self._round = _round

    @property
    def shape(self) -> Tuple[int, ...]:
        return HEIGHT, WIDTH

    @property
    def coordinates(self) -> Mapping[Union[str, Coordinates], Union[Number, Tuple[Number, Number]]]:
        return {
            Coordinates.X: round_to_x()[0],
            Coordinates.Y: round_to_y()[0],
            Coordinates.Z: round_to_z(self._round)[0],
        }

    @property
    def format(self) -> ImageFormat:
        return ImageFormat.TIFF

    def tile_data(self) -> np.ndarray:
        return np.ones((HEIGHT, WIDTH), dtype=np.float32)


def test_scalar_coordinates():
    """Set up an ImageStack where only a single scalar physical coordinate is provided per axis.
    Internally, this should be converted to a range where the two endpoints are identical to the
    physical coordinate provided.
    """
    stack = ImageStack.synthetic_stack(
        NUM_ROUND, NUM_CH, NUM_Z,
        HEIGHT, WIDTH,
        tile_fetcher=tile_fetcher_factory(
            ScalarTiles,
            True,
        )
    )

    for selectors in stack._iter_axes({Axes.ROUND, Axes.CH, Axes.ZPLANE}):
        expected_x = round_to_x()[0]
        expected_y = round_to_y()[0]
        expected_z = round_to_z(selectors[Axes.ROUND])[0]

        verify_physical_coordinates(
            stack,
            selectors,
            (expected_x, expected_x),
            (expected_y, expected_y),
            (expected_z, expected_z),
        )
