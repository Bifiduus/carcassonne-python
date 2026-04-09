# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
PYTHON        ?= python
SPHINXOPTS    ?=
SPHINXBUILD   ?= $(PYTHON) -m sphinx
SPHINXAPIDOC  ?= $(PYTHON) -m sphinx.ext.apidoc
SOURCEDIR     = source
BUILDDIR      = build
PACKAGEDIR    = ../carcassonne

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile apidoc html

apidoc:
	@$(SPHINXAPIDOC) --implicit-namespaces -f -o "$(SOURCEDIR)" "$(PACKAGEDIR)"

html: apidoc
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
