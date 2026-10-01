from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from .maintenance import MaintenanceBusy, lock, state


class EditionMaintenanceMiddleware(MiddlewareMixin):
    """Placed before sessions so the gate also spans session persistence."""

    def process_request(self, request):
        base = "/" + settings.ADMIN_URL.strip("/") + "/"
        request._edition_control = request.path.startswith(
            base + "edition_management/editionrun/"
        )
        if request._edition_control:
            return None
        request._edition_lock = lock()
        try:
            request._edition_lock.__enter__()
        except MaintenanceBusy:
            request._edition_lock = None
            return HttpResponse(
                "Edition maintenance is in progress. Please retry later.", status=503
            )
        return None

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request._edition_control:
            return (
                None  # Every control endpoint independently verifies superuser access.
            )
        phase = state().phase
        if phase == "open":
            return None
        base = "/" + settings.ADMIN_URL.strip("/") + "/"
        if request.path in (base + "login/", base + "logout/"):
            return None
        user = request.user
        if (
            phase == "prepared"
            and request.path.startswith(base)
            and user.is_active
            and user.is_staff
            and user.is_superuser
        ):
            return None
        return HttpResponse("The portal is closed for edition preparation.", status=503)

    def process_response(self, request, response):
        gate = getattr(request, "_edition_lock", None)
        if gate is not None:
            gate.__exit__(None, None, None)
        return response
