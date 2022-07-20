from django.views.generic import ListView

from procurement.models import Tender


class HomePageView(ListView):
    context_object_name = "tenders"
    template_name = "procurement/home.html"

    def get_queryset(self):
        return Tender.objects.filter(value__gt=0)[:100]
