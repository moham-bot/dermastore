from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "لوحة تحكم متجر ريمشي الطبي"
admin.site.site_title = "ريمشي"
admin.site.index_title = "مرحباً بك في لوحة التحكم"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
