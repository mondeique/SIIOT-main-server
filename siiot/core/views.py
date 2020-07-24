from django.http import HttpResponseRedirect


def download_link(request):
    return HttpResponseRedirect('https://play.google.com/store/apps/details?id=com.mondeique.siiot')