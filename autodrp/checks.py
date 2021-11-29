class TestCheck:
    def __init__(self, parent_check=None):
        self.parent_check = parent_check

    def has_permission(self, request):
        print(f'Permission (GLOBAL) ran for {request}')

        if self.parent_check and hasattr(self.parent_check, 'has_permission'):
            return self.parent_check.has_permission(request)

        return False

    def has_object_permission(self, request, obj):
        print(f'Permission (OBJECT) ran for {request} {obj}')

        if self.parent_check and hasattr(self.parent_check, 'has_object_permission'):
            return self.parent_check.has_object_permission(request, obj)

        return False
    
    def filter(self, request, queryset):
        print(f'Filter ran for {request} {queryset}')

        if self.parent_check and hasattr(self.parent_check, 'filter'):
            queryset, filtered = self.parent_check.filter(request, queryset)
            print(f'Filtered queryset: {queryset}')
            return queryset, filtered

        return queryset, False

class ModelAttributeCheck:
    def __init__(self, *args, enable_obj_permission=False, **kwargs):
        self.args = [arg for arg in args if not hasattr(arg, 'filter')]
        self.filters = [arg for arg in args if hasattr(arg, 'filter')]
        self.kwargs = kwargs
        if enable_obj_permission:
            self.has_object_permission = self._has_object_permission
    
    def has_permission(self, request):
        return True
    
    def _compile_args(self, request):
        args = [value if not callable(value) else value(request) for value in self.args]
        kwargs = {key: (value if not callable(value) else value(request)) for key, value in self.kwargs.items()}
        return args, kwargs

    def _has_object_permission(self, request, obj):
        args, kwargs = self._compile_args(request)
        return obj.model.objects.filter(args, pk=obj.pk, **kwargs).exists()

    def filter(self, request, queryset):
        args, kwargs = self._compile_args(request)
        queryset = queryset.filter(*args, **kwargs)
        for _filter in self.filters:
            queryset, filtered = _filter.filter(request, queryset)
        return queryset, True

class IsAuthenticated:
    def __init__(self, filter=None):
        self._filter = filter

    def has_permission(self, request):
        return request.user.is_authenticated

    def has_object_permission(self, request, obj):
        if self._filter and hasattr(self._filter, 'has_object_permission'):
            return self._filter.has_object_permission(request, obj)
        return True

    def filter(self, request, queryset):
        if self._filter:
            return self._filter.filter(request, queryset)
        return queryset, False

class IsAnonymous:
    def __init__(self, filter=None):
        self._filter = filter

    def has_permission(self, request):
        return request.user.is_anonymous

    def has_object_permission(self, request, obj):
        if self._filter and hasattr(self._filter, 'has_object_permission'):
            return self._filter.has_object_permission(request, obj)
        return True

    def filter(self, request, queryset):
        if self._filter:
            return self._filter.filter(request, queryset)
        return queryset, False

class QueryParamSwitch:
    def __init__(self, *cases, else_case=None):
        self.cases = cases
        self.else_case = else_case
    
    def filter(self, request, queryset):
        for case in self.cases:
            if case['param'](request.query_params):
                return case['filter'].filter(request, queryset)
        if self.else_case:
            return self.else_case.filter(request, queryset)
        return queryset.none(), True
