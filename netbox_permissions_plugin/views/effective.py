"""View for "Effective permissions for user"."""

from __future__ import annotations

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.views import View

from ..forms import EffectiveQueryForm
from ..resolver.effective import compute_effective


class EffectivePermissionsView(PermissionRequiredMixin, View):
    """User picker -> aggregated list of their permissions."""

    permission_required = "users.view_objectpermission"
    template_name = "netbox_permissions_plugin/effective.html"

    def get(self, request):
        form = EffectiveQueryForm(request.GET or None)
        result = None
        if request.GET and form.is_valid():
            user = form.cleaned_data["user"]
            result = compute_effective(user)
        return render(
            request,
            self.template_name,
            {"form": form, "result": result},
        )
