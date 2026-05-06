"""PluginTemplateExtension — добавляет вкладку «Permissions» на детальную
страницу любого объекта NetBox с reverse_lookup-таблицей.

Регистрируется через `template_extensions` в PluginConfig.
В этапе 1 показываем результат reverse_lookup без action-фильтра — чтобы
сразу был виден полный список доступов.
"""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from netbox.plugins import PluginTemplateExtension

from .resolver.reverse import reverse_lookup


class _ObjectPermissionsTab(PluginTemplateExtension):
    """Базовый класс — конкретные models задаются в подклассах."""

    def right_page(self):
        obj = self.context["object"]
        ct = ContentType.objects.get_for_model(obj.__class__)
        rows = reverse_lookup(ct, obj.pk)
        return self.render(
            "netbox_permissions_plugin/_object_tab.html",
            extra_context={"perm_rows": rows},
        )


# Список моделей, к которым подключаем tab. Можно расширять по мере надобности
# или сделать цикл по всем NetBoxModel. Для MVP — наиболее частые.
_TARGETS = [
    "dcim.device",
    "dcim.site",
    "dcim.rack",
    "ipam.prefix",
    "ipam.ipaddress",
    "tenancy.tenant",
    "virtualization.virtualmachine",
    "circuits.circuit",
    "extras.script",
]


def _make_extensions() -> list[type[PluginTemplateExtension]]:
    extensions: list[type[PluginTemplateExtension]] = []
    for label in _TARGETS:
        cls = type(
            f"PermissionsTab__{label.replace('.', '_')}",
            (_ObjectPermissionsTab,),
            {"models": [label]},
        )
        extensions.append(cls)
    return extensions


template_extensions = _make_extensions()
