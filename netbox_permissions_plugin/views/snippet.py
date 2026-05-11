"""Standard NetBox CRUD views for ``ConstraintSnippet``.

NetBox's ``generic`` module ships per-action class-based views that handle
the common machinery: pagination, filter sidebar, bulk-edit/delete, audit
logging, htmx-aware rendering, etc. We just hook our model / form / table /
filterset into them.
"""

from __future__ import annotations

from netbox.views import generic

from ..filtersets import ConstraintSnippetFilterSet
from ..forms import ConstraintSnippetFilterForm, ConstraintSnippetForm
from ..models import ConstraintSnippet
from ..tables import ConstraintSnippetTable


class ConstraintSnippetListView(generic.ObjectListView):
    queryset = ConstraintSnippet.objects.all()
    table = ConstraintSnippetTable
    filterset = ConstraintSnippetFilterSet
    filterset_form = ConstraintSnippetFilterForm


class ConstraintSnippetView(generic.ObjectView):
    queryset = ConstraintSnippet.objects.all()


class ConstraintSnippetEditView(generic.ObjectEditView):
    queryset = ConstraintSnippet.objects.all()
    form = ConstraintSnippetForm


class ConstraintSnippetDeleteView(generic.ObjectDeleteView):
    queryset = ConstraintSnippet.objects.all()


class ConstraintSnippetBulkDeleteView(generic.BulkDeleteView):
    queryset = ConstraintSnippet.objects.all()
    table = ConstraintSnippetTable
    filterset = ConstraintSnippetFilterSet
