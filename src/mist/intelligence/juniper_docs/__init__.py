"""Juniper documentation corpus harvester package.

This package downloads the United States and English Juniper documentation
corpus to local disk. It reads the sitemap index, builds a document inventory,
keeps the newest release note in each train, resolves one companion PDF for
each document root, downloads each PDF, and sorts each file into a category.
For a document that matches no slug keyword, the package reads a bounded PDF
text sample in memory, derives a sub-category label from content signals, and
then discards the text.

The package holds five real children: ``models`` and the four sub-packages
``discovery``, ``acquire``, ``classify``, and ``harvest``.
"""
