from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('programs/', views.programs, name='programs'),
    path('licence-test/', views.licence_test, name='licence_test'),
    path('gallery/', views.gallery, name='gallery'),
    path('programs/program1/', views.program1, name='program1'),
    path('programs/program2/', views.program2, name='program2'),
    path('programs/program3/', views.program3, name='program3'),
    path('programs/program4/', views.program4, name='program4'),
    path('ilfen-test/', views.ilfen_test_view, name='ilfen_test'),
    path('junior_ilfen-test/', views.junior_ilfen_test_view, name='junior_ilfen_test'),
    path('test-registration/', views.TestRegistrationView.as_view(), name='test_registration'),
    path('take-test/', views.take_test, name='take_test'),
    path('test-result/', views.test_result, name='test_result'),
    path('download-certificate/', views.download_certificate, name='download_certificate'),

    path('director/login/', views.director_login, name='director_login'),
    path('director/logout/', views.director_logout, name='director_logout'),
    path('director/dashboard/', views.director_dashboard, name='director_dashboard'),
    path('director/questions/', views.question_list, name='question_list'),
    path('director/questions/create/', views.question_create, name='question_create'),
    path('director/questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('director/questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
    path('director/traits/', views.trait_list, name='trait_list'),
    path('director/traits/create/', views.trait_create, name='trait_create'),
    path('director/traits/<int:pk>/edit/', views.trait_edit, name='trait_edit'),
    path('director/traits/<int:pk>/delete/', views.trait_delete, name='trait_delete'),
    path('director/results/', views.test_results, name='test_results'),

    # Junior Test URLs
    path('junior-test-registration/', views.JuniorTestRegistrationView.as_view(), name='junior_test_registration'),
    path('junior-take-test/', views.junior_take_test, name='junior_take_test'),
    path('junior-test-result/', views.junior_test_result, name='junior_test_result'),
    path('junior-download-certificate/', views.junior_download_certificate, name='junior_download_certificate'),

    # Junior Questions URLs
    path('director/junior-questions/', views.junior_question_list, name='junior_question_list'),
    path('director/junior-questions/create/', views.junior_question_create, name='junior_question_create'),
    path('director/junior-questions/<int:pk>/edit/', views.junior_question_edit, name='junior_question_edit'),
    path('director/junior-questions/<int:pk>/delete/', views.junior_question_delete, name='junior_question_delete'),

    # Junior Traits URLs
    path('director/junior-traits/', views.junior_trait_list, name='junior_trait_list'),
    path('director/junior-traits/create/', views.junior_trait_create, name='junior_trait_create'),
    path('director/junior-traits/<int:pk>/edit/', views.junior_trait_edit, name='junior_trait_edit'),
    path('director/junior-traits/<int:pk>/delete/', views.junior_trait_delete, name='junior_trait_delete'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)