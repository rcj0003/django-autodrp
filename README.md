# django-autodrp
Automatically set-up filters and permissions for Django's DRY Rest Permissions

# Quick Start
1. Run `pip install django-autodrp`
2. Add 'autodrp' to your INSTALLED_APPS in your settings below all the apps you wish to use AutoDRP for (failing to add django-autodrp after the apps that will use it will result in the autoconfiguration of AutoDRP not running).
```python
INSTALLED_APPS = [
  # Django apps / packages
  'all-django-apps',
  # Your apps
  'yourapp'
]
```

```python
INSTALLED_APPS = [
  # Django apps / packages
  'all-django-apps',
  # Your apps
  'yourapp',
  'autodrp', # <- Here
]
```
3. Add the following (or replace your already existing has_blank_permission functions) to any models you with to use AutoDRP for (either is optional):
```python
DRY_GLOBAL_PERMISSIONS = {
     ('read', 'write'): True
}

DRY_OBJECT_PERMISSIONS = {
     ('read', 'write'): True
}
```
Indicating `read` with a value of true is the same as:
```python
@staticmethod
def has_read_permission(request):
     return True
```

4. Import `AutoDRPFilter` via `from autodrp.filters import AutoDRPFilter`, and add it to your `filter_backends` on your viewset like so:
```python
from autodrp.filters import AutoDRPFilter

class ProjectViewSet(viewsets.ModelViewset):
  queryset = Project.objects.all()
  permission_classes = (DRYPermissions,)
  filter_backends = [AutoDRPFilter]
```
5. You now are using AutoDRP permissions and filters.

# Motivation for this project
I've found DRY Rest Permissions to be a great asset but rather verbose. I hope to make working with DRY Rest Permissions easier by consolidating filter and permission functionality into a simple and terse feature.
