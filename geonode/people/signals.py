from django.dispatch import receiver, Signal

request_add_organization_signal = Signal(providing_args=["form"])
