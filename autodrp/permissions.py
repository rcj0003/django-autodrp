from rest_framework import permissions


class AutoDRPSerializerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        serializer_class = view.get_serializer_class()
        meta = getattr(serializer_class, 'Meta', None)

        if meta and hasattr(meta, 'has_permission'):
            return meta.has_permission(request)

        return False
    
    def has_object_permission(self, request, view, obj):
        serializer_class = view.get_serializer_class()
        meta = getattr(serializer_class, 'Meta', None)

        if meta and hasattr(meta, 'has_object_permission'):
            return meta.has_object_permission(request, obj)

        return False