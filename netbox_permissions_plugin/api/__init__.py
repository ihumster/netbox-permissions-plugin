"""REST API for the plugin's models.

Required by NetBox 4.x even if we don't yet expose endpoints to users:
``netbox.utilities.api.get_serializer_for_model`` is called on every
``NetBoxModel.save()`` to serialize the instance for the event queue
(webhooks, change journaling). Without a serializer NetBox raises
``SerializerNotFound`` and the save fails.

The serializers here are also the basis for the introspection /
preview / writeable API endpoints we will add in stage 2 PR C and PR D.
"""
