from django.db.models.signals import class_prepared
from django.dispatch import receiver

ALWAYS_TRUE = lambda *args, **kwargs: True

class CheckPermissions:
    def __init__(self, *checks):
        self.checks = checks
    
    def __call__(self, request):
        for permission in self.checks:
            if permission.has_permission(request):
                return True
        return False

class CheckObjectPermissions:
    def __init__(self, *checks):
        self.checks = checks
    
    def __call__(self, obj, request):
        for permission in self.checks:
            if permission.has_object_permission(request, obj):
                return True
        return False

class Filter:
    def __init__(self, *checks):
        self.checks = checks
    
    def __call__(self, request, queryset):
        for filter in self.checks:
            if hasattr(filter, 'has_permission') and not filter.has_permission(request):
                continue

            queryset, filtered = filter.filter(request, queryset)
            
            if filtered:
                break
        
        return queryset

def _bake_global_permissions(sender, permission_data):
    for actions, check_data in permission_data.items():
        if not hasattr(check_data, '__iter__'):
            check_data = [check_data]
        
        checks = [check for check in check_data if hasattr(check, 'has_permission')]
        actions = [actions] if isinstance(actions, str) else actions

        if len(checks) > 0:
            permission_function = staticmethod(CheckPermissions(*checks))
        else:
            permission_function = staticmethod(ALWAYS_TRUE)

        for action in actions:
            setattr(sender, f'has_{action}_permission', permission_function)

def _bake_object_permissions(sender, permission_data):
    for actions, check_data in permission_data.items():
        if not hasattr(check_data, '__iter__') and not isinstance(check_data, str):
            check_data = [check_data]
        
        checks = [check for check in check_data if hasattr(check, 'has_object_permission')]
        filters = [check for check in check_data if hasattr(check, 'filter')]
        actions = [actions] if isinstance(actions, str) else actions

        if len(checks) > 0:
            permission_function = CheckPermissions(*checks)
        else:
            permission_function = ALWAYS_TRUE

        for action in actions:
            setattr(sender, f'has_object_{action}_permission', permission_function)
        
        if len(filters) > 0:
            filter_function = staticmethod(Filter(*filters))
            for action in actions:
                setattr(sender, f'filter_for_{action}', filter_function)

def bake_permissions(sender):
    if hasattr(sender, '_bake_permission_data'):
        _bake_global_permissions(sender, sender._bake_permission_data())
    elif hasattr(sender, 'DRY_GLOBAL_PERMISSIONS'):
        _bake_global_permissions(sender, sender.DRY_GLOBAL_PERMISSIONS)

    if hasattr(sender, '_bake_object_permission_data'):
        _bake_object_permissions(sender, sender._bake_object_permission_data())
    elif hasattr(sender, 'DRY_OBJECT_PERMISSIONS'):
        _bake_object_permissions(sender, sender.DRY_OBJECT_PERMISSIONS)
