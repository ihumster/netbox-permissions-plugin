"""Plugin's own database models.

* ``ConstraintSnippet`` -- a reusable JSON constraint fragment that the
  builder UI can insert into an ObjectPermission's ``constraints`` field.
* ``PermissionAuditEvent`` -- an immutable log of plugin actions
  (effective-permissions queries, ObjectPermission writes, snippet edits,
  dry-runs) kept independently of NetBox's built-in ``extras.ObjectChange``.

Both models are imported here so Django's app loader picks them up via the
default ``app_label`` from ``apps.py``. Direct submodule imports
(``from netbox_permissions_plugin.models.snippet import ConstraintSnippet``)
are equally valid -- both styles work.
"""

from __future__ import annotations

from .audit import ActionType, PermissionAuditEvent
from .snippet import ConstraintSnippet

__all__ = [
    "ActionType",
    "ConstraintSnippet",
    "PermissionAuditEvent",
]
