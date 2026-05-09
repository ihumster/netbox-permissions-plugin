"""View for "Who has access to object X"."""

from __future__ import annotations

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.views import View

from ..forms import ReverseQueryForm
from ..resolver.reverse import reverse_lookup


class ReverseLookupView(PermissionRequiredMixin, View):
    permission_required = "users.view_objectpermission"
    template_name = "netbox_permissions_plugin/reverse.html"

    def get(self, request):
        form = ReverseQueryForm(request.GET or None)
        rows = None
        target_repr = None
        if request.GET and form.is_valid():
            ct = form.cleaned_data["object_type"]
            object_id = form.cleaned_data["object_id"]
            action = form.cleaned_data["action"] or None
            rows = reverse_lookup(ct, object_id, action=action)
            model = ct.model_class()
            if model is not None:
                obj = model._default_manager.filter(pk=object_id).first()
                if obj is not None:
                    target_repr = str(obj)
        return render(
            request,
            self.template_name,
            {"form": form, "rows": rows, "target_repr": target_repr},
        )
