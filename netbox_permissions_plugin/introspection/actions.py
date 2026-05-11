"""Discovery of actions applicable to a set of ContentTypes.

Returns:

* the four standard CRUD actions (``view``, ``add``, ``change``, ``delete``),
  always applicable to any model;
* custom actions registered for specific CTs. In stage 2 PR A we hard-code
  the only one your prod uses -- ``run`` for ``extras.Script`` -- plus a
  small, future-proof shape so additional custom actions (e.g. plugins'
  own actions) can be registered without code changes elsewhere.

The wider discovery (scanning ``netbox.registry`` for plugin-registered
permissions) is deferred to a later PR -- the registry API has shifted
across NetBox minors and we do not need the breadth right now. The
builder UI in stage 2 PR D will additionally accept free-form custom
action names from the user, so unknown actions are not blocked.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from .types import ActionDescriptor

if TYPE_CHECKING:  # pragma: no cover
    from django.contrib.contenttypes.models import ContentType


# Standard CRUD actions. These map 1:1 to Django ``auth.Permission`` codenames
# (``view_<model>``, ``add_<model>``, ``change_<model>``, ``delete_<model>``)
# and are universally applicable.
_STANDARD_ACTIONS = ("view", "add", "change", "delete")


# Custom actions that are tied to a specific CT in stock NetBox 4.x.
# Format: { ct_label -> [(action_name, source_label), ...] }.
_CT_BOUND_CUSTOM_ACTIONS: dict[str, list[tuple[str, str]]] = {
    "extras.script": [("run", "extras.Script")],
}


def list_actions_for_cts(content_types: Iterable[ContentType]) -> dict[str, ActionDescriptor]:
    """Return all actions applicable to the union of ``content_types``.

    Keyed by action name so callers can dedupe naturally; the value carries
    the metadata the builder UI needs (label, source, applicable CTs).
    """
    result: dict[str, ActionDescriptor] = {}

    # Standard CRUD -- emitted once, applies to every CT.
    for name in _STANDARD_ACTIONS:
        result[name] = ActionDescriptor(
            name=name,
            label=name,
            is_standard=True,
            applicable_cts=("*",),
            source="django.builtin",
        )

    # CT-bound custom actions. Iterate the provided CTs and pick up anything
    # registered against them; collect ``applicable_cts`` per action so a
    # single action that targets multiple CTs (rare, but possible) ends up
    # with the right list.
    custom_acc: dict[str, set[str]] = {}
    custom_source: dict[str, str] = {}
    for ct in content_types:
        ct_label = f"{ct.app_label}.{ct.model}"
        for action_name, source_label in _CT_BOUND_CUSTOM_ACTIONS.get(ct_label, ()):
            custom_acc.setdefault(action_name, set()).add(ct_label)
            custom_source.setdefault(action_name, source_label)

    for action_name, cts in custom_acc.items():
        result[action_name] = ActionDescriptor(
            name=action_name,
            label=action_name,
            is_standard=False,
            applicable_cts=tuple(sorted(cts)),
            source=custom_source[action_name],
        )

    return result
