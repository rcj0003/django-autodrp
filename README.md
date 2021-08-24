# django-autodrp
Automatically set-up filters and permissions for Django's DRY Rest Permissions

# Getting Started
1. Install AutoDRP
2. Add 'django-autodrp' to your INSTALLED_APPS in your settings above all the apps you wish to use AutoDRP for (failing to add django-autodrp before the apps that will use it will result in the autoconfiguration of AutoDRP not running).
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
  'autodrp', # <- Here
  # Your apps
  'yourapp'
]
```

4. AutoDRP will now automatically configure the models to use DRY Rest Permissions

# Using AutoDRP to configure DRY Rest Permissions
***This assumes you have knowledge of using DRY Rest Permissions***


To get started with AutoDRP, add the following to your model you will be using DRY Rest Permissions for:
```python
DRY_GLOBAL_PERMISSIONS = {
}

DRY_OBJECT_PERMISSIONS = {
}
```
This data will be used to automatically configure your model to use DRY Rest Permissions.

Now, let's say you want the user to always have permission to read a model. You can achieve this by doing the following:
```python
DRY_GLOBAL_PERMISSIONS = {
  'read': True
}
```
Adding that to the dictionary is equivalent to doing the following:
```python
def has_read_permission(self, request):
  return True
```

Functionality is not limited to just that however. What if I wanted the user to be able to read models with certain attributes only? For this example, let's suppose the following model exists:
```python
class Project(models.Model):
  name = models.CharField(max_length=64)
  is_active = models.BooleanField(default=True)
```
We want a user to be able to read all projects that are active. We can achieve this like so:
```python
from autodrp import models as drp

class Project(models.Model):
  name = models.CharField(max_length=64)
  is_active = models.BooleanField(default=True)
  
  DRY_GLOBAL_PERMISSIONS = {
    'read': True
  }

  DRY_OBJECT_PERMISSIONS = {
    'read': drp.ModelAttributeCheck(is_active=True)
  }
```
Now, DRY Rest Permissions will do the proper checks to see if the user has access to the model (when calling `self.get_object()` on a viewset). AutoDRP will then handle the checks that it generated on configuration of the model.


This functionality is not the only functionality offered by AutoDRP. AutoDRP will take the same object permission checks and configure them for filtering. Let's assume you have a viewset like so:
```python
class ProjectViewSet(viewsets.ModelViewset):
  queryset = Project.objects.all()
```
This viewset has the basic actions, like list, retrieve, etc. because it is a ModelViewset. Right now, a user would theoretically be able to see every Project via the `list` endpoint, but when calling the `retrieve` endpoint, you would get a 403 Unauthorized for projects that aren't active. Let's fix this using AutoDRP's other feature, which is filtering.
```python
from autodrp.filters import AutoDRPFilter

class ProjectViewSet(viewsets.ModelViewset):
  queryset = Project.objects.all()
  filter_backends = [AutoDRPFilter]
```
Now, when you visit the `list` endpoint for the `ProjectViewSet`, only active projects will be listed.

### Next Steps
Let's take this a little further. Let's assume that we want users to be able to see all projects if they are authenticated, only active projects if they are not authenticated, to disable deletion of all projects, and to allow updating of a project if authenticated. We can achieve this like so:
```python
from autodrp import models as drp

class Project(models.Model):
  name = models.CharField(max_length=64)
  is_active = models.BooleanField(default=True)
  
  DRY_GLOBAL_PERMISSIONS = {
    'read': True,
    'destroy': False,
    ('write', 'create'): drp.AuthenticatedCheck(),
  }

  DRY_OBJECT_PERMISSIONS = {
    'read': (
      drp.AuthenticatedCheck(),
      drp.ModelAttributeCheck(is_active=True)
    )
  }
```
Some of this will likely require explanation. You may notice `('write', 'create')`. In order to reduce some of the verbosity of AutoDRP, AutoDRP accepts standard iterables (list, tuple, set) and will automatically generate the necessary functions for each. This not only reduces vebosity, but also saves some space by reusing the same data.


You may also notice that multiple checks were specified for the object read permission. AutoDRP allows for multiple cases to occur for each permission check. In this example, AutoDRP will first check to see if the user is authenticated. If they are, then nothing is filtered for the project queryset that will be returned when using `self.get_queryset()` on a viewset. If the user is not authenticated, AutoDRP will move on to the next check. The check will return true, and the queryset will be filtered by Project's `is_active`.

### More About Checks
Let's assume the same scenario as above, albeit with some tweaks. We only want authenticated users to be able to view projects that are active. Unauthenticated users will only be able to view projects that start with "Public". This can be done with a few tweaks:
```python
from autodrp import models as drp

class Project(models.Model):
  name = models.CharField(max_length=64)
  is_active = models.BooleanField(default=True)
  
  DRY_GLOBAL_PERMISSIONS = {
    'read': True,
    'destroy': False,
    ('write', 'create'): drp.AuthenticatedCheck(),
  }

  DRY_OBJECT_PERMISSIONS = {
    'read': (
      drp.AuthenticatedCheck(
        filter=drp.ModelAttributeCheck(is_active=True)
      ),
      drp.ModelAttributeCheck(name__startswith='Public')
    )
  }
```
Some AutoDRP checks take filters that will be used if the check is true. However, this could've also been accomplished like so:
```python
from autodrp import models as drp

class Project(models.Model):
  name = models.CharField(max_length=64)
  is_active = models.BooleanField(default=True)
  
  DRY_GLOBAL_PERMISSIONS = {
    'read': True,
    'destroy': False,
    ('write', 'create'): drp.AuthenticatedCheck(),
  }

  DRY_OBJECT_PERMISSIONS = {
    'read': (
      drp.RequireAll(
        drp.AuthenticatedCheck(),
        drp.ModelAttributeCheck(is_active=True)
      ),
      drp.ModelAttributeCheck(name__startswith='Public')
    )
  }
```
The `RequireAll` check does exactly what it sounds like. It takes arguments for checks and requires that all associated checks return true, or doesn't pass the check. If it passes, the filter will filter based on each passed in check. In this case, AuthenticatedCheck doesn't do any filtering on its own, so the only filter applied to the queryset returned in `self.get_queryset()` on your viewset is the check to see if the project is active.


`RequireAll` is generally useful for combining filters and permission checks.

# Writing Your Own Checks
Writing your own check is a rather straightforward process. A basic check should look something like this:
```python
class Check:
  def has_permission(self, request):
    return True
   
  def has_object_permission(self, request, obj):
    return True

  def filter(self, request, queryset):
    return queryset
```
A check can omit any of those methods. Maybe you only want to check to see if a project is active, but not filter the projects. In that case, a check can be written with `has_permission` and `has_object_permission`, but excludes the `filter` method. You may find that writing a method for `has_object_permission` for a check like ModelAttributeCheck can be a hassle and might not be able to be done in an efficient manner. Or maybe you just would like to check to see if a user is authenticated, but not filter anything. Those are potential use cases of omitting some of the methods.


In effect, this check would do nothing. Let's continue to work with the previous example and show how we can write a check that only allows active projects to be viewed by authenticated users:
```python
class ProjectVisibleCheck:
  def has_permission(self, request):
    return request.user.is_authenticated

  def has_object_permission(self, request, project):
    return project.is_active

  def filter(self, request, queryset):
    return queryset.filter(is_active=True)
```
Now, authenticated users can view active projects only. Now we can use our check in the configuration of AutoDRP like so:

```python
from autodrp import models as drp

class ProjectVisibleCheck:
  def has_permission(self, request):
    return request.user.is_authenticated

  def has_object_permission(self, request, project):
    return project.is_active

  def filter(self, request, queryset):
    return queryset.filter(is_active=True)

class Project(models.Model):
  name = models.CharField(max_length=64)
  is_active = models.BooleanField(default=True)
  
  DRY_GLOBAL_PERMISSIONS = {
    'read': True,
    'destroy': False,
    ('write', 'create'): drp.AuthenticatedCheck(),
  }

  DRY_OBJECT_PERMISSIONS = {
    'read': (
      ProjectVisibleCheck(),
      drp.ModelAttributeCheck(name__startswith='Public')
    )
  }
```
This essentially does the same thing as before, but the logic can now be reused in other places. In most cases, simply using the existing AutoDRP checks will suffice, but the functionality is there if you need it.


However, maybe you have a custom instance of Django's user model and wanted to check to see if the account was an admin account. Let's assume the following is what we are using for our Django user account:
```python
class Account(AbstractBaseUser):
    email = models.EmailField(blank=False, unique=True, max_length=64)
    is_admin = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
```
Let's write a check that will give admins permission to destroy a project:
```python
class AdminCheck:
  def has_permission(self, request):
    return request.user.is_admin
```
Now we will add this check to the Project model:
```python
from autodrp import models as drp

class AdminCheck:
  def has_permission(self, request):
    return request.user.is_admin

class ProjectVisibleCheck:
  def has_permission(self, request):
    return request.user.is_authenticated

  def has_object_permission(self, request, project):
    return project.is_active

  def filter(self, request, queryset):
    return queryset.filter(is_active=True)

class Project(models.Model):
  name = models.CharField(max_length=64)
  is_active = models.BooleanField(default=True)
  
  DRY_GLOBAL_PERMISSIONS = {
    'read': True,
    'destroy': AdminCheck(),
    ('write', 'create'): drp.AuthenticatedCheck(),
  }

  DRY_OBJECT_PERMISSIONS = {
    'read': (
      ProjectVisibleCheck(),
      drp.ModelAttributeCheck(name__startswith='Public')
    )
  }
```
Now, admins can destroy a project, and projects cannot be deleted by non-admin and unauthenticated users.


# Final Notes
I've found DRY Rest Permissions to be a great asset but rather verbose. I hope to make working with DRY Rest Permissions easier by consolidating filter and permission functionality into a simple and terse feature.
