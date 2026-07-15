from django.apps import AppConfig


class NotificacaoConfig(AppConfig):
    name = 'notificacao'

    def ready(self):
        import notificacao.signals
