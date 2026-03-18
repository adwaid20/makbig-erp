from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def superadmin_required(view_func):

    @login_required(login_url='staff_login')
    @wraps(view_func)
    def wrapper(request,*args, **kwargs):
        if not request.user.is_superadmin:
            raise PermissionDenied
        return view_func(request,*args, **kwargs)
    return wrapper