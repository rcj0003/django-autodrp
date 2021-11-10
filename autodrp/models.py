from django.db import models


class AutoDRPModel(models.Model):
    @classmethod
    def _bake_permission_data(cls):
        return cls.DRY_GLOBAL_PERMISSIONS
    
    @classmethod
    def _bake_object_permission_data(cls):
        return cls.DRY_OBJECT_PERMISSIONS

    class Meta:
        abstract = True
