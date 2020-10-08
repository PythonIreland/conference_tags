import itertools
import math


def make_batches(iterable, n):
    iterable = iter(iterable)
    n_rest = n - 1

    for item in iterable:
        rest = itertools.islice(iterable, n_rest)
        yield itertools.chain((item,), rest)


def two_per_page(data):
    """ used to keep tickets ordering after page cut"""
    size = len(data)
    nb_pages = math.ceil(size / 2.0)
    for i in range(int(nb_pages)):
        yield i, data[i]
        if i + nb_pages < size:
            yield i + nb_pages, data[i + nb_pages]
