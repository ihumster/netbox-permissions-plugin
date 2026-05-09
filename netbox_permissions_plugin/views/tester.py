"""View for "Permission tester": single allow/deny check with a trace."""

from __future__ import annotations

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.views import View

from ..forms import TesterForm
from ..resolver.tester import explain


class TesterView(PermissionRequiredMixin, View):
    permission_required = "users.view_objectpermission"
    template_name = "netbox_permissions_plugin/tester.html"

    def get(self, request):
        form = TesterForm(request.GET or None)
        result = None
        if request.GET and form.is_valid():
            result = explain(
                user=form.cleaned_data["user"],
                content_type=form.cleaned_data["object_type"],
                object_id=form.cleaned_data["object_id"],
                action=form.cleaned_data["action"],
            )
        return render(
            request,
            self.template_name,
            {"form": form, "result": result},
        )
