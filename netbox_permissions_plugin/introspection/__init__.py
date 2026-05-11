"""Introspection layer for the constraint builder.

Pure-Python helpers that, given a ContentType, return:

* the list of fields available on the model (native ORM fields + custom fields
  from ``extras.CustomField``), with type info, FK targets, choices, and a
  hint about which ORM lookups are sensible for each field;
* the list of actions applicable to that ContentType (standard CRUD plus
  custom actions like ``run`` for ``extras.Script``).

This is the data the future visual constraint builder (stage 2 PR D) will
consume via AJAX. The introspection layer itself is HTTP-free; an API layer
will wrap it in PR D where the builder needs JSON over the wire.

Per the same pattern as ``resolver/``, this ``__init__.py`` does not
re-export submodules so the package can be imported without triggering
heavy Django apps-registry loads. Import directly:

    from netbox_permissions_plugin.introspection.fields import list_fields
    from netbox_permissions_plugin.introspection.actions import list_actions_for_cts
    from netbox_permissions_plugin.introspection.types import FieldDescriptor, ActionDescriptor
"""
