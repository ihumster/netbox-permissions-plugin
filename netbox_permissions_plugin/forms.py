"""Формы для трёх аудит-страниц.

Используем нативные NetBox-поля (DynamicModelChoiceField), чтобы получить
красивый поиск с autocomplete для пользователей и ContentType.
"""

from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from utilities.forms.fields import DynamicModelChoiceField

User = get_user_model()


class EffectiveQueryForm(forms.Form):
    user = DynamicModelChoiceField(
        queryset=User.objects.all(),
        required=True,
        label="Пользователь",
        help_text="Чьи эффективные права вычислить.",
    )


class ReverseQueryForm(forms.Form):
    object_type = DynamicModelChoiceField(
        queryset=ContentType.objects.order_by("app_label", "model"),
        required=True,
        label="Тип объекта",
    )
    object_id = forms.IntegerField(
        required=True,
        min_value=1,
        label="ID объекта",
        help_text="Числовой PK объекта в БД.",
    )
    action = forms.CharField(
        required=False,
        max_length=50,
        label="Action (опционально)",
        help_text="Если пусто — учитываются все actions.",
    )


class TesterForm(forms.Form):
    user = DynamicModelChoiceField(
        queryset=User.objects.all(),
        required=True,
        label="Пользователь",
    )
    object_type = DynamicModelChoiceField(
        queryset=ContentType.objects.order_by("app_label", "model"),
        required=True,
        label="Тип объекта",
    )
    object_id = forms.IntegerField(
        required=True,
        min_value=1,
        label="ID объекта",
    )
    action = forms.CharField(
        required=True,
        max_length=50,
        label="Action",
        help_text="view / add / change / delete / run / любой кастомный.",
    )
