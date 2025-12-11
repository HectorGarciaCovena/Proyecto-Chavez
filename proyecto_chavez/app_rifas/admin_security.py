from django.contrib import messages
from django.contrib.auth import authenticate
from django.shortcuts import render, redirect
from django.urls import reverse
from django.template.response import TemplateResponse


class SecureDeleteMixin:
    """
    Mixin para requerir la contraseña del usuario antes de eliminar.
    Se utiliza en el admin para cualquier modelo sensible.
    """

    confirm_delete_template = "admin/security_confirm_delete.html"

    def delete_model(self, request, obj):
        """
        Este método solo se ejecuta si ya pasó la verificación.
        """
        super().delete_model(request, obj)
        messages.success(request, f"🗑 Registro eliminado correctamente: {obj}")

    def delete_view(self, request, object_id, extra_context=None):
        """
        Sobrescribe el delete_view para solicitar contraseña manualmente.
        """
        obj = self.get_object(request, object_id)

        if obj is None:
            messages.error(request, "El objeto no existe.")
            return redirect("..")

        if request.method == "POST" and "password" in request.POST:
            password = request.POST.get("password")

            user = authenticate(username=request.user.username, password=password)

            if user:
                # AUTORIZADO
                return super().delete_view(request, object_id, extra_context)

            # CONTRASEÑA INCORRECTa ❌
            messages.error(request, "❌ Contraseña incorrecta.")

        # Mostrar formulario de contraseña
        context = {
            **self.admin_site.each_context(request),
            "object": obj,
            "opts": self.model._meta,
            "cancel_url": f"../",
        }

        return TemplateResponse(request, self.confirm_delete_template, context)


