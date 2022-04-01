from django.utils.decorators import available_attrs
from functools import wraps

def passes_test_then_return_func(test_func, return_func):
    """
    Check if test_func returns true then call return_func as response, 
    otherwise proceed normally.
    Modified from django/contrib/auth/decorators.py:user_passes_test()
    """

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request):
                return return_func(request)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
