from ._baking import _bake_object_methods, _bake_global_permission_method


def bake_serializer_permissions(cls):
    class_meta = getattr(cls, 'Meta', None)

    if class_meta:
        if hasattr(class_meta, '_bake_permission_data'):
            permission_data = class_meta._bake_permission_data()
        elif hasattr(class_meta, 'DRY_GLOBAL_PERMISSIONS'):
            permission_data = class_meta.DRY_GLOBAL_PERMISSIONS
        else:
            raise Exception('Missing "_bake_permission_data" method or "DRY_GLOBAL_PERMISSIONS" attribute!')
        
        permission_function = _bake_global_permission_method(permission_data)
        setattr(class_meta, 'has_permission', permission_function)

        if hasattr(class_meta, '_bake_object_permission_data'):
            object_permission_data = class_meta._bake_object_permission_data()
        elif hasattr(class_meta, 'DRY_OBJECT_PERMISSIONS'):
            object_permission_data = class_meta.DRY_OBJECT_PERMISSIONS
        else:
            raise Exception('Missing "_bake_object_permission_data" method or "DRY_OBJECT_PERMISSIONS" attribute!')
        
        permission_function, filter_function = _bake_object_methods(object_permission_data)
        setattr(class_meta, 'has_object_permission', permission_function)
        if filter_function:
            setattr(class_meta, 'filter', filter_function)
    else:
        raise Exception('Serializer must have "Meta" class to bake permissions!')

    return cls