import django.apps
from django.apps import AppConfig

from autodrp.utils import bake_permissions


class AutoDRPConfig(AppConfig):
    name = 'autodrp'

    def ready(self):
        for model in django.apps.apps.get_models():
            bake_permissions(model)
