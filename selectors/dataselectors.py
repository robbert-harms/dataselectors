"""This module provides a set of higher level selectors than those in the base module.

Most of these need to be localized to your problem domain. With localization, we mean that the column name
used by the selector may need to be modified to fit your dataframe.
"""

__author__ = 'Robbert Harms'
__date__ = '2024-04-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from typing import Callable, Self

import numpy as np
import pandas as pd

from dataselectors.base import DataSelectorQuery, DataSelector, LocalizableSelector, AbstractDataSelector


class Sex(LocalizableSelector, DataSelectorQuery):
    column_name: str = 'sex'

    def __init__(self, sex: int | str = 'male'):
        """Select on a desired sex in your dataset.

        By default, this searches in the column named "sex". To change this, subclass or use the "with_class"
        method.

        Args:
            sex: we support the following cases:
                0 or "female": females
                1 or "male": males
                2 or "other": for non-binary
                3 or "unknown": for known missing data
        """
        if sex == 0 or sex == 'female':
            super().__init__(f'`{self.column_name}` == 0')
        elif sex == 1 or sex == 'male':
            super().__init__(f'`{self.column_name}` == 1')
        elif sex == 2 or sex == 'other':
            super().__init__(f'`{self.column_name}` == 2')
        elif sex == 3 or sex == 'unknown':
            super().__init__(f'`{self.column_name}` == 3')
        else:
            raise ValueError(f'Unknown sex {sex} provided.')


class Age(LocalizableSelector, DataSelectorQuery):
    column_name = 'age'

    def __init__(self, age: int):
        """Select all subjects of a specific age.

        Args:
            age: the specific age we want to select
        """
        super().__init__(f'`{self.column_name}` == {age}')


class RangeQuery(LocalizableSelector, DataSelectorQuery):

    def __init__(self,
                 min_value: int | float | None = None,
                 max_value: int | float | None = None,
                 min_inclusive: bool = True,
                 max_inclusive: bool = False):
        """In the column provided by the localization superclass, search all values within the range specified.

        This uses the pandas query method, as such floating point numbers will be converted to strings to search.

        By default, this selects including the minimum, excluding the maximum value, i.e. selects ``[min, max)``.
        This can easily be changed by setting the flags for including min or max.

        Args:
            min_value: the minimum value to select
            max_value: the maximum value to select
            min_inclusive: if we include the minimum value or not  (i.e. ``>`` vs ``>=``).
            max_inclusive: if we include the maximum value or not  (i.e. ``<`` vs ``<=``).
        """
        self._min_value = min_value
        self._max_value = max_value
        self._min_inclusive = min_inclusive
        self._max_inclusive = max_inclusive

        if self._min_value is None and self._max_value is None:
            raise ValueError('At least a minimum or a maximum value must be specified.')

        min_selector = '>'
        if min_inclusive:
            min_selector = '>='

        max_selector = '<'
        if max_inclusive:
            max_selector = '<='

        if self._max_value is None:
            super().__init__(DataSelectorQuery(f'`{self.column_name}` {min_selector} {min_value}'))
        elif self._min_value is None:
            super().__init__(DataSelectorQuery(f'`{self.column_name}` {max_selector} {max_value}'))
        else:
            super().__init__(DataSelectorQuery(f'`{self.column_name}` {min_selector} {min_value}')
                             & DataSelectorQuery(f'`{self.column_name}` {max_selector} {max_value}'))


class UniqueElements(AbstractDataSelector):

    def __init__(self, column_name: str, indexer: Callable[[pd.DataFrame], int] | None = None):
        """Create a list of unique rows by selecting a single row for each unique element in a column.

        Args:
            column_name: the name of the column to search in
            indexer: an optional indexing function to choose which row to return for each unique element.
                Provided with a dataframe of sessions, return the local index within 1..N of the session we want to use.
        """
        self._column_name = column_name
        self._indexer = indexer

    def get_indices(self, df: pd.DataFrame) -> pd.Index:
        def selector(df_group):
            if self._indexer:
                try:
                    return df_group.index[self._indexer(df_group)]
                except IndexError:
                    raise IndexError('The indexer function does not provide an index for all groups.')
            else:
                return df_group.index[0]

        return pd.Index(df.groupby(self._column_name).apply(selector).values)


class HasValue(DataSelectorQuery):

    def __init__(self, column_name: str):
        """Returns all rows for which the provided column has a value (i.e. is not nan).

        Args:
            column_name: the column to check on
        """
        super().__init__(f'{column_name} == {column_name}')


class Sample(AbstractDataSelector):

    def __init__(self,
                 nmr_rows: int,
                 base_selector: DataSelector | None = None,
                 replace: bool = False,
                 seed: int | None = None):
        """Randomly sample N rows from the dataset.

        It is possible to provide a base selector which we will apply before we will sample.

        If the number of subjects in the dataframe, possibly after selecting using the base selector,
        is less than N, we return the entire dataframe or base group selection.

        Args:
            nmr_rows: the number of rows to sample
            base_selector: the selector defining the group from which we want to sample N subjects.
            replace: if we want to select with replacement
            seed: the random state used in the sampling.
        """
        self.nmr_rows = nmr_rows
        self.base_selector = base_selector
        self.replace = replace
        self.seed = seed

    def with_base_selector(self, base_selector: DataSelector | None = None) -> Self:
        """Create a new instance of this selector with the given base selector as base.

        Args:
            base_selector: the new base selector, or None if needed

        Returns:
            A new instance of this selector
        """
        return type(self)(self.nmr_rows, base_selector=base_selector, replace=self.replace, seed=self.seed)

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.base_selector:
            data = self.base_selector.apply(df)
        else:
            data = df

        if len(data) < self.nmr_rows:
            return data

        np.random.seed(self.seed)
        return data.iloc[np.random.choice(len(data), self.nmr_rows, replace=self.replace)]

    def get_indices(self, df: pd.DataFrame) -> pd.Index:
        if self.base_selector:
            indices = self.base_selector.get_indices(df)
        else:
            indices = df.index

        if len(indices) < self.nmr_rows:
            return indices

        np.random.seed(self.seed)
        return pd.Index(np.random.choice(indices, self.nmr_rows, replace=self.replace))

    def __lt__(self, other: DataSelector) -> Self:
        """Create a new instance of this selector using the provided selector as base.

        By overriding this operator we allow composition of this selector using the `<` symbol, which we may interpret
        as a data flow operator. We can then write ``Sample() < Selector()``, meaning we use the data of the "Selector"
        as base class for this selector.

        Using this function will create a new selector with the piped in selector as base.

        Args:
            other: the selector to use as base

        Returns:
            A new selector of this type with the other selector as base.
        """
        return self.with_base_selector(other)

    def __gt__(self, other) -> Self:
        """Create a new instance of this selector using the provided selector as base.

        By overriding this operator we allow composition of this selector using the `>` symbol, which we may interpret
        as a data flow operator. We can then write ``Selector() > Sample()``, meaning we use the data of the "Selector"
        as base class for the "Sample" selector.

        Using this function will create a new selector with the piped in selector as base.

        Args:
            other: the selector to use as base

        Returns:
            A new selector of this type with the other selector as base.
        """
        return self.with_base_selector(other)
