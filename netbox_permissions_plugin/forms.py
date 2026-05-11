"""Forms for the three audit pages and the plugin's own models.

User picker is NetBox's ``DynamicModelChoiceField`` (autocompletes via the users
REST API). ContentType picker is ``ContentTypeChoiceField`` -- a regular dropdown
with "app_label | model" labels. We cannot use ``DynamicModelChoiceField`` for
ContentType because Django's ``contenttypes`` app has no REST API namespace
in NetBox; the dynamic field tries to reverse ``contenttypes-api:contenttype-list``
which raises ``NoReverseMatch``.

Model-bound forms (``ConstraintSnippetForm``, ``...FilterForm``) extend NetBox
form bases so list pages get the standard filter sidebar / search box.
"""

from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import (
    ContentTypeChoiceField,
    ContentTypeMultipleChoiceField,
    DynamicModelChoiceField,
)

from .models import ConstraintSnippet

User = get_user_model()


class EffectiveQueryForm(forms.Form):
    user = DynamicModelChoiceField(
        queryset=User.objects.all(),
        required=True,
        label="User",
        help_text="Whose effective permissions to compute.",
    )


class ReverseQueryForm(forms.Form):
    object_type = ContentTypeChoiceField(
        queryset=ContentType.objects.order_by("app_label", "model"),
        required=True,
        label="Object type",
    )
    object_id = forms.IntegerField(
        required=True,
        min_value=1,
        label="Object ID",
        help_text="Numeric primary key of the object in the database.",
    )
    action = forms.CharField(
        required=False,
        max_length=50,
        label="Action (optional)",
        help_text="Leave empty to consider all actions.",
    )


class TesterForm(forms.Form):
    user = DynamicModelChoiceField(
        queryset=User.objects.all(),
        required=True,
        label="User",
    )
    object_type = ContentTypeChoiceField(
        queryset=ContentType.objects.order_by("app_label", "model"),
        required=True,
        label="Object type",
    )
    object_id = forms.IntegerField(
        required=True,
        min_value=1,
        label="Object ID",
    )
    action = forms.CharField(
        required=True,
        max_length=50,
        label="Action",
        help_text="view / add / change / delete / run / any custom action.",
    )


# ---------------------------------------------------------------------------
# ConstraintSnippet forms
# ---------------------------------------------------------------------------


class ConstraintSnippetForm(NetBoxModelForm):
    """Create / edit form for ``ConstraintSnippet``.

    The ``body`` field is exposed as a textarea over the underlying JSONField;
    validation in ``ConstraintSnippet.clean()`` rejects shapes that are not
    a JSON object or an array of objects, so this form does not duplicate
    the rule. NetBox renders JSON inputs nicely on submit.
    """

    object_types = ContentTypeMultipleChoiceField(
        queryset=ContentType.objects.order_by("app_label", "model"),
        required=False,
        label="Applicable to",
        help_text="Leave empty to make the snippet available for any CT.",
    )

    class Meta:
        model = ConstraintSnippet
        fields = ("name", "description", "body", "object_types", "tags")


class ConstraintSnippetFilterForm(NetBoxModelFilterSetForm):
    """Filter form for the snippet list page (sidebar)."""

    model = ConstraintSnippet

    object_types = ContentTypeMultipleChoiceField(
        queryset=ContentType.objects.order_by("app_label", "model"),
        required=False,
        label="Applicable to",
    )
