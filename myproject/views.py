from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from api.models import URLMapping

# def redirect_url(request, short_key):
#     try:
#         mapping = get_object_or_404(URLMapping, short_url=short_key)
#         return redirect(mapping.long_url)
#     except Exception as e:
#         return HttpResponse(f"Error: {e}", status=404)

def test_view(request):
    return HttpResponse("Route matched!")
