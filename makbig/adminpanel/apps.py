from django.apps import AppConfig


class AdminpanelConfig(AppConfig):
    name = 'adminpanel'


    def ready(self):
        import adminpanel.signals