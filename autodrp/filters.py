from rest_framework.filters import BaseFilterBackend


class AutoDRPFilter(BaseFilterBackend):
    def __init__(self, *args, imply_missing_rw_perms=True, **kwargs):
        self.imply_missing_rw_perms = imply_missing_rw_perms
        super().__init__(*args, **kwargs)
    
    def _do_filter(self, request, action, queryset):
        qs_filter = getattr(queryset.model, f'filter_for_{action}', None)

        if qs_filter:
            return qs_filter(request, queryset), True
        
        return queryset, False

    def filter_queryset(self, request, queryset, view):
        queryset, filtered = self._do_filter(request, view.action, queryset)

        if not filtered and self.imply_missing_rw_perms:
            if request.method.lower() == 'get':
                queryset, filtered = self._do_filter(request, 'read', queryset)
            else:
                queryset, filtered = self._do_filter(request, 'write', queryset)

        return queryset
