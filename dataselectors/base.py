"""Type, abstract base classes, and other base classes for data selectors.

This is the abstract foundation upon which the data selectors are build.
"""
from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2024-04-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'


from abc import ABCMeta, abstractmethod
from typing import Self, Type
import pandas as pd


class DataSelector(metaclass=ABCMeta):
    """Data selectors encapsulate the definition of a selection of data from a dataset.

    This is a type class for all data selectors.

    When using this base class, data selectors can be combined using union, intersection and complement
    operators implemented as `|`, `&`, and `~`.
    """

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply this data selector to the provided dataframe.

        Args:
            df: the dataframe from which to select a subset

        Returns:
            The result of the data selector on the provided dataframe.
        """

    @abstractmethod
    def get_indices(self, df: pd.DataFrame) -> pd.Index:
        """Get the indices of the data selector applied on the provided dataframe.

        Args:
            df: the dataframe on which to operate

        Returns:
            The selected indices
        """

    @abstractmethod
    def __and__(self, other: DataSelector) -> Self:
        """Set theoretic intersection of two data selectors.

        Args:
            other: the other data selector to intersect with this selector

        Returns:
             A new data selector representing the intersection of this one and the other.
        """

    @abstractmethod
    def __or__(self, other: DataSelector) -> Self:
        """Set theoretic union of two data selectors.

        Args:
            other: the other data selector to combine with this one in an union.

        Returns:
             A new data selector representing the union of this one and the other.
        """

    @abstractmethod
    def __invert__(self) -> Self:
        """Set theoretic complement of this data selector.

        Returns:
             A new data selector with the set theoretic complement of this selector.
        """


class AbstractDataSelector(DataSelector, metaclass=ABCMeta):
    """Implements the ``apply`` method of the base data selector by using the ``get_indices`` method. """

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.loc[self.get_indices(df)]

    def __and__(self, other: DataSelector) -> IntersectionDataSelector:
        return IntersectionDataSelector(self, other)

    def __or__(self, other: DataSelector) -> UnionDataSelector:
        return UnionDataSelector(self, other)

    def __invert__(self) -> ComplementedDataSelector:
        return ComplementedDataSelector(self)


class DataSelectorQuery(AbstractDataSelector):

    def __init__(self, query: str | DataSelectorQuery):
        """Data selector using a pandas query expression string.

        Having these as a separate base class allows us to optimize some selections since we can combine the
        selectors in a single pandas query string. As a fallback, we can use the generic combination classes.

        Args:
            query: the query to use for the apply method
        """
        if isinstance(query, DataSelectorQuery):
            self.query = query.query
        else:
            self.query = query

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.query(self.query)

    def get_indices(self, df: pd.DataFrame) -> pd.Index:
        return df.query(self.query).index

    def __and__[T: DataSelector | DataSelectorQuery](self, other: T) -> T:
        if isinstance(other, DataSelectorQuery):
            return DataSelectorQuery(f'(({self.query}) & ({other.query}))')
        return super().__and__(other)

    def __or__[T: DataSelector | DataSelectorQuery](self, other: T) -> T:
        if isinstance(other, DataSelectorQuery):
            return DataSelectorQuery(f'(({self.query}) | ({other.query}))')
        return super().__or__(other)

    def __invert__(self) -> DataSelectorQuery:
        return DataSelectorQuery(f'~({self.query})')


class IntersectionDataSelector(AbstractDataSelector):

    def __init__(self, left_selector: DataSelector, right_selector: DataSelector):
        """Create the intersection of two data selectors.

        This operator shortcuts to the left, that is, it first takes the left subset and applies the
        right selector on that subset.

        Args:
            left_selector: the left set of data
            right_selector: the right set of data
        """
        self._left_selector = left_selector
        self._right_selector = right_selector

    def get_indices(self, df: pd.DataFrame) -> pd.Index:
        left_indices = self._left_selector.get_indices(df)
        return self._right_selector.get_indices(df.loc[left_indices])


class UnionDataSelector(AbstractDataSelector):

    def __init__(self, left_selector: DataSelector, right_selector: DataSelector):
        """Create the union of two data selectors.

        Args:
            left_selector: the left set of data
            right_selector: the right set of data
        """
        self._left_selector = left_selector
        self._right_selector = right_selector

    def get_indices(self, df: pd.DataFrame) -> pd.Index:
        left_indices = self._left_selector.get_indices(df)
        right_indices = self._right_selector.get_indices(df)
        return left_indices.union(right_indices)


class ComplementedDataSelector(AbstractDataSelector):

    def __init__(self, data_selector: DataSelector):
        """Created a complemented data selector.

        This complements a selector by selecting all elements the original selector would not select.

        Args:
            data_selector: the data selector we wish to complement
        """
        self._data_selector = data_selector

    def get_indices(self, df: pd.DataFrame) -> pd.Index:
        return df.index[~df.index.isin(self._data_selector.get_indices(df))]

    def __invert__(self) -> Self:
        if isinstance(self, ComplementedDataSelector):
            return self._data_selector
        return super().__invert__()


class LocalizableSelector(DataSelector, metaclass=ABCMeta):
    """A base class for selectors which can be localized to a specific column.

    By having this as a class attribute we can easily create subclasses without having to pass the column name
    in the constructor. Furthermore, you can create subclasses utilizing a specific column name using three methods.

    Method 1, specify the column name in the class definition::

        class MySelector(LocalizableSelector, column_name='<my_column>'):
            pass

    Method 2, set the column name using the ``column_name`` attribute:

        class MySelector(LocalizableSelector):
            column_name = '<my_column>'

    Method 3, use the `get_localized` class method to generate a new localized class:

        class MySelector(LocalizableSelector.get_localized('<my_column>'))

    Where '<my_column>' is of course the name of your desired column name.

    Which to use depends on your preference.

    Attributes:
        column_name: the name of the column the implementing class will use for its functionality.
    """
    column_name: str

    def __init_subclass__(cls, /, column_name: str | None = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if column_name is not None:
            cls.column_name = column_name

    @classmethod
    def get_localized(cls, column_name: str) -> Type[Self]:
        """Get a new class of the same type as this, with the column name set to the given value.

        This basically creates a new class with the given column name as default and returns that class.

        Args:
            column_name: the new column name for the new generated class

        Returns:
            A class (not an instance) of the same type as this class.
        """
        class LocalizedClass(cls, column_name=column_name):
            pass
        return LocalizedClass
