import django.apps
from django.apps import AppConfig

from ._baking import bake_class_permissions


class AutoDRPConfig(AppConfig):
    name = 'autodrp'

    def ready(self):
        for model in django.apps.apps.get_models():
            bake_class_permissions(model)
