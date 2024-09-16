__author__ = 'Robbert Harms'
__date__ = '2024-04-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from typing import Any

import numpy as np
import pandas as pd

from dataselectors.base import DataSelector


def label_rows(df: pd.DataFrame, labelled_selectors: dict[Any, DataSelector], dtype: str = 'object') -> pd.Series:
    """Label the rows of a dataframe according to the provided data selectors.

    This function may be interpreted as colouring the elements of a dataframe with a set of labels. The dataselectors
    are used to determine the grouping and then the elements are given one of the labels.

    If, for a given row the data selectors are not mutually exclusive, a random label may be returned.

    Args:
        df: the dataframe to apply the data selectors to
        labelled_selectors: the labels with their respective data selectors.
        dtype: the dtype to use for the new series, defaults to object

    Returns:
        A series with NA values for rows without a selector, and else a label based on the data selectors.
    """
    labels = pd.Series(index=df.index, dtype=dtype)
    for label, data_selection in labelled_selectors.items():
        labels[data_selection.get_indices(df)] = label
    return labels


def group_rows(df: pd.DataFrame,
               dataselectors: list[DataSelector],
               allow_overlap: bool = True) -> pd.Series:
    """Label a dataframe with linear integer labels, based on the provided data selectors.

    If for a given row the data selectors are not mutually exclusive, a random index may be returned.

    Args:
        df: the dataframe to apply the data selectors to
        dataselectors: the data selectors by which we group the data
        allow_overlap: if we allow overlapping groups, if set to False we raise an exception if the groups overlap

    Returns:
        A series with pd.NA values for rows without a selector, and else an index based on the data selection.

    Raises:
        ValueError: if the groups overlap while they should not
    """
    if not allow_overlap and not are_disjoint_groups(df, dataselectors):
        raise ValueError('The data selectors overlap.')

    indices = pd.Series(index=df.index, dtype="Int64")
    for ind, data_selection in enumerate(dataselectors):
        indices[data_selection.get_indices(df)] = ind

    return indices


def are_disjoint_groups(df: pd.DataFrame, dataselectors: list[DataSelector]) -> bool:
    """Check if the provided data selectors are disjoint groups.

    If for a given row the data selectors are not mutually exclusive, a random index may be returned.

    Args:
        df: the dataframe to apply the data selectors to
        dataselectors: the data selectors by which we group the data

    Returns:
        True if the groups are disjoint, false otherwise.
    """
    indices = []
    for data_selection in dataselectors:
        indices.append(data_selection.get_indices(df))

    all_indices = np.hstack(indices)
    return len(all_indices) == len(np.unique(all_indices))
