from django.apps import AppConfig


class BolaoConfig(AppConfig):
    name = 'bolao'

    def ready(self):
        import bolao.signals
