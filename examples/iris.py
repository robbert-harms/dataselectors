__author__ = 'Robbert Harms'
__date__ = '2024-04-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'


import pandas as pd
from dataselectors.selectors import RangeQuery, UniqueElements, Sample
from dataselectors.utils import label_rows

"""First we define some selectors to use in our Iris dataset example.

Users of this library are encouraged to predefine their selectors and test them for correctness.

We will showcase various ways of creating range query selectors.
"""

# Defining a class directly as a localized version of a range query
SepalLengthRange = RangeQuery.get_localized('sepal.length')


# Using a localized range query as base class
class SepalWidthRange(RangeQuery.get_localized('sepal.width')):
    pass


# Using class arguments to specify the column name to localize to
class PetalLengthRange(RangeQuery, column_name='petal.length'):
    pass


# set the column name directly in the new class
class PetalWidthRange(RangeQuery):
    column_name = 'petal.width'


"""Loading the dataset and run some queries"""
df_iris = pd.read_csv('iris.csv')

# selecting elements with a sepal length of [-, 5) | [6, -), i.e. excluding [5, 6)
ds_box = (SepalLengthRange(max_value=5) | SepalLengthRange(min_value=6))
print(ds_box.apply(df_iris))

# the same selection as before, but now stated as a complement
ds_box2 = ~SepalLengthRange(min_value=5, max_value=6)
print(ds_box2.apply(df_iris))

# sample elements from the box defined earlier, all three definitions below are equal
sampler1 = Sample(5, base_selector=ds_box, seed=0)
sampler2 = Sample(5, seed=0) < ds_box
sampler3 = ds_box > Sample(5, seed=0)

print(sampler1.apply(df_iris))
print(sampler2.apply(df_iris))
print(sampler3.apply(df_iris))

# selecting the second instance of each unique variety
unique_variety = UniqueElements('variety', lambda df: 2)
print(unique_variety.apply(df_iris))

# getting the index of a selection without selecting
print(unique_variety.get_indices(df_iris))

# create nominal labels based on the petal length
petal_length_labels = label_rows(df_iris, {'short_petal': PetalLengthRange(max_value=3),
                                           'medium_petal': PetalLengthRange(min_value=3, max_value=6),
                                           'long_petal': PetalLengthRange(min_value=6)}, dtype='string')
df_iris['petal.length.nominal'] = petal_length_labels
print(df_iris)
