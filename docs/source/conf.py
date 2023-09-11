# Configuration file for the Sphinx documentation builder.

# -- Project information

project = "LDSA Portal"
copyright = "2023, LDSA DevOps Team"
author = "LDSA DevOps Team"

version = "0.2.0"
release = "0.1"

# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "rtd": ("https://docs.readthedocs.io/en/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# -- Options for EPUB output
epub_show_urls = "footnote"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output
html_theme = "sphinx_rtd_theme"


