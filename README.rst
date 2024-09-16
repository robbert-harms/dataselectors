##############
Data selectors
##############
This package provides a framework for data selectors to be used with Pandas dataframes.
These data selectors allow you to separate concept and execution of data selection,
by declaring up front a range of data selections you later wish to apply on a Pandas dataframe.
Utilizing concepts from set theory, data selectors can be combined at will to expand, or narrow the scope of a selection.

************
Introduction
************
The major concept of this library is that you declare your data selections before you use them.
To explain this concept, let us first take a step back and investigate what we mean with data selection.

Suppose that you are running a medical study and you gathered data like heart rate, medicine use,
alcohol intake, smoking habits, age, sex, level of education, etc.
You loaded this data in a Pandas dataframe using aptly named columns (heart_rate, medicine_use, nmr_alcohol_week, etc.).
Now, you wish to select some of these subjects for your analysis.
For instance, you wish to select all subjects older than 50 with a low heart rate.
One way to do this is by direct selection of your data, like so:

.. code-block:: python

    df_selection = df[(df['age'] >= 50) & (df['heart_rate'] < 60)]

Here, ``df`` is assumed to be your pandas dataframe.

Another method is by using Pandas queries to select your data, like so:

.. code-block:: python

    df_selection = df.query('(age >= 50) & (heart_rate < 60)')

In both cases, you will end up with a subset of your original dataframe, with only the subjects
within your selection. Here, your selection was (age >= 50, heart rate < 60),
and the result of applying this selection gives you our selected data.

While the above works and is fast and easy to type, it has several disadvantages.
To start, when you change the name of your columns, you will have to change this column name in
every query you created. You could use search and replace, but you may easily miss a query if
you have a large script. A second disadvantage is that the above methods only works for simple selections.
More difficult selections like "find all subjects who have a follow-up exam after two months after the first"
can not be so simply stated and probably require a new function.
Creating higher level selections is error prone and more difficult to combine with the selections above.
A third and final disadvantage of the shown selection methods is that they are difficult to
reuse. Unless you create a function making the selection, you would have to type your selection
again in multiple places.

Data selectors
==============
Data selectors abstract the notion of defining a selection from actually selecting data.
In its most simplest form it could amount to a single function:

.. code-block:: python

    def select_analysis_subjects(df: pd.Dataframe) -> pd.Dataframe:
        return df.query('(age >= 50) & (heart_rate < 60)')


This function takes in a dataframe and provides a dataframe, with the body of the function defining a data selection.
By doing so, we created a reusable function which we can easily expand with more complex parts if needed, and it ideally
gives us only one location to change if we change column names.

While this works, it may not be fully reusable.
If you want a different heart rate selected in a second analysis,
you will either have to add arguments to the function to make the queries variable,
or copy the function and change parts.
Second, if you are only interested in the indices and not
the actual data, you again would have to change the function to return the indices instead of the data.

A different approach, and the approach taken by this library is to make classes for the various
parts of a selection you wish to apply.
For instance, for our example study we could create a selector ``AgeRange``,
and a selector ``HeartRateRange``.
These selectors would abstract away the column name of the data and have methods for
returning either the data, or the index.
For example, for ``AgeRange`` it could look something like this:

.. code-block:: python

    class AgeRange(DataSelector):

        def __init__(self, min_age: int, max_age: int):
            self._min_age = min_age
            self._max_age = max_age

        def apply(self, df: pd.DataFrame) -> pd.DataFrame:
            return df.query(f'(age >= {self._min_age}) & (age < {self._max_age})')

        def get_indices(self, df: pd.DataFrame) -> pd.Index:
            return ... # get the indices of the selection


With ``HeartRateRange`` looking very similar except a different class name and variable name.
The base ``DataSelector`` is used as a base type for all selectors, we will get to that later.

To use the ``AgeRange`` class, we would type:

.. code-block:: python

    age_selector = AgeRange(min_age=50, max_age=100)
    df_selection = age_selector.apply(df)


In this example, we first instantiated our age range selector, and later applied it to our
dataframe to get our selected data. This is the crucial part of this library, separate the concept of the selection
from the execution of the selection.

This class based method has several advantages over the other methods shown.
First of all, it encapsulates the knowledge of a specific selector, i.e. to use a selector
you only need to know *what* it does, not *how* it does it.
Second, it allows for upfront definitions, making the selectors testable and verifiable.
Third, it allows for type hinting. You can create functions expecting a ``DataSelector`` as input.
Finally, you do not need to search and replace all your scripts when you rename the name of a column in your data.
To change class names you can often use your editor tools to change the name of the class everywhere for you.

Combining selectors
===================
We have now developed the idea of data selectors and we can create selectors for different purposes like
data ranges (HeartRateRange, AgeRange), nominal variables (Sex (m/f/x)), or for complex selections
like "subjects who have a follow-up exam after two months after the first".
What is missing is a way to combine these selectors.

To combine various selectors we will utilize some concepts from set theory, intersection, union and complements.
In an intersection we are interested in elements that two sets have in common.
With a union we want to combine all elements of two sets.
Complementation asks to select all elements outside of a specific set.
We will apply these concepts to the selectors themselves, to create new selectors representing
the act of combining data using intersection, union, or complementation.
In essence, we can create sentences in a selectors mini-language.

Suppose that for our earlier example we already created data selectors for age, sex, and heart rate, and we
wish to combine these in various ways for different parts of the analysis.
Using set theory we could create selectors like this:

.. code-block:: python

    selection_1 = AgeRange(min_age=50) & HeartRateRange(max_rate=60)
    selection_2 = ((Sex('female') & AgeRange(min_age=50))
                   | (Sex('male') & AgeRange(min_age=60)))
    selection_3 = ~(Sex('unknown') | Sex('x'))

In words, these selectors represent:

#. Minimum age 50 and heart rate lower than 60
#. All females above 50, combined with all males above 60
#. All subjects for whom the sex is known and not generic (i.e. select males and females).

These selectors themselves could easily be combined again as well:

.. code-block:: python

    selection_4 = (selection_1 | selection_2) & selection_3

To create a complex selection of specific subjects.

Above can easily be implemented in Python using operator overloading of the ``__and__``, ``__or__``, and ``__invert__`` class methods.
This is exactly what this library does for you whenever you subclass from ``DataSelector``.

Using selectors
===============
After you have defined your selector, application is as simple as calling the ``apply`` method to get the data selection, or
calling the ``get_indices`` method get the index selection.

A different way to use the selectors is to use them as declarations and pass them to functions.
For instance, suppose you run various classification models and you created a class to represent
these different models. This could look like:

.. code-block:: python

    class YoungAgeModel(ModelDefinition):
        class0_sel = Parkinson(False) & AgeRange(max=30)
        class1_sel = Parkinson(True) & AgeRange(max=30)
        classifier = XGBoost(eta=0.2)

    class OldAgeModel(ModelDefinition):
        class0_sel = Parkinson(False) & AgeRange(min=60)
        class1_sel = Parkinson(True) & AgeRange(min=60)
        classifier = XGBoost(eta=0.5)

Having defined these models, application could be by using a function like:

.. code-block:: python

    def train_model(data: pd.DataFrame, model: ModelDefinition) -> TrainedModel:
        ...


This function would accept a dataset and a model definition, and would train the classifier
defined in the model definition on the data selected by the selectors in the model definition.

What have we gained by doing so? Encapsulation of a classification model,
reusability, generability and testability.


**********
Python API
**********
The API consists of several layers of abstraction, first a base layer defined in ``dataselectors.base`` and
second several layers of abstraction in prepared selectors in ``dataselectors.selectors``.

Base classes
============
The first layer consists of a few base classes you can use to create your own custom selectors.
These classes are:

.. code-block:: python

    from dataselectors.base import (DataSelector, AbstractDataSelector,
                                     DataSelectorQuery, LocalizableSelector)

The basic type for all selectors is ``DataSelector``.
Any selector should in some way implement this base type. Any code using data selectors my
use this type as a type hint.
The second class is ``AbstractDataSelector``, this is an abstract implementation of a the basic type
providing some methods with a default operation, only keeping the ``get_indices`` method open
for implementing classes to implement.
Finally, ``DataSelectorQuery`` can be used as a base class for operations that can be expressed as a pandas query.
In some scenarios this provides some speed benefits over using the ``AbstractDataSelector`` class as starting point.
``LocalizableSelector`` is a selector meant to be used in conjunction with either
``AbstractDataSelector`` or ``DataSelectorQuery`` and provides for column name localization.

Simple selectors
================
The second layer of abstraction is formed by simple data selectors.
These selectors implement either ``AbstractDataSelector`` or ``DataSelectorQuery`` and provide some sort of selection.
An example of such as selector is the ``UniqueElements`` selector which selects all unique elements for a given column.

This can be used as:

.. code-block:: python

    from dataselectors.selectors import UniqueElements

    unique_income = UniqueElements('income')
    unique_income.apply(df)

In essence it functions similar to Pandas's "drop_duplicates" only then wrapped as a data selector meaning we can compose it with other selectors.


Localizable selectors
=====================
A third layer of abstraction is formed by the localizable selectors.
These selectors all inherit from ``LocalizableSelector`` and provide some functionality for a
specific column.
For instance, the ``RangeQuery`` selector allows selecting rows in a specific column with values
between a certain given minimum and maximum value.
For instance, if you want to create a selector for age ranges, you can do so as:

.. code-block:: python

    from dataselectors.selectors import RangeQuery
    class AgeRange(RangeQuery, column_name='age'):
        pass

What this does is create a new class ``AgeRange``, from base class ``RangeQuery``, operating on column "age".
Now, you can use this age range as such:

.. code-block:: python

    age_selector = AgeRange(min_value=10, max_value=30)
    age_selector.apply(df)

Which creates a selector using the age range and applies this on some data in `df`.


Meta selectors
==============
A fourth level of selectors is provided by the meta selectors.
These selectors can use another selector in the constructor to augment the
selection in various ways.

As an example of a meta selector, we can look at the ``Sample`` selector.
This selector can create a sample of N rows of your dataset.
It optionally takes another selector as argument in the constructor.
This optional base selector will then be used to create a base selection to use for the sampling.

For instance, suppose we want to get a random selection of all persons in a specific age range.
We would do so as such:

.. code-block:: python

    from dataselectors.selectors import Sample

    age_selector = AgeRange(min_value=10, max_value=30)
    sample_age_selector = Sample(10, base_selector=age_selector)
    sample_age_selector.apply(df)


Here, we reused our previously defined age selector and used it as a basis for the sample selector.
This sample selector will select 10 random rows from the data after the age selector has been applied.
If you want a sample of 10 rows without any other selection you can simply use:

.. code-block:: python

    from dataselectors.selectors import Sample

    sample_selector = Sample(10)
    sample_selector.apply(df)

This will just sample 10 rows from your data.


Your own selectors
==================
Of course it does not end here.
Using all these base classes it is hopefully easy to implement your own selectors specific to your data investigation.
If you created a data selector which you think is useful to the community, consider sharing it with me and we will put it in this library.


Utility functions
=================
The module ``dataselectors.utils`` contains a few utility functions for data selectors.
These include some functions to label rows according to groups defined with data selectors,
and contains a function to check if two selectors return disjoint groups.

Examples
========
See the directory `examples` for sparkling your creativity with this library.

**********
Conclusion
**********
In this package we set forth the idea of separating the concept and execution of data selection.
We introduced data selectors and have shown how these can be combined using set theoretic operators for intersection, union and complementation.
By creating your own data selectors, or specializing those from this library, users will be able to customize data selectors for their own projects.
These selectors help to create generic, reusable and verifiable data selections, exactly what data science projects require.
