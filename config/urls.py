from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # FAQRAT BIRTA "" YO'L BO'LISHI KERAK!
    path('', include('home.urls')),  # home ilovasi - ASOSIY YO'L
    
    # Qo'shimcha HTML sahifalar
    path('admin.html', TemplateView.as_view(template_name='admin.html'), name='admin_html'),
    path('admin-page/', TemplateView.as_view(template_name='admin.html'), name='admin_page'),
    path('student.html', TemplateView.as_view(template_name='student.html'), name='student_html'),
    path('student/', TemplateView.as_view(template_name='student.html'), name='student'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)