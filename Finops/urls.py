from django.urls import path
from .views import register_user_api, apply_loan_api, make_payment_api, get_statement_api, index, signin, logout

urlpatterns = [
    path('', index, name='index'),
   path('signup', register_user_api, name='signup'),
    path('api/apply-loan/', apply_loan_api, name='apply_loan_api'),
    path('api/make-payment/', make_payment_api, name='make_payment_api'),
    path('api/get-statement/', get_statement_api, name='get_statement_api'),
    path('signin',signin, name='signin'),
    path('logout',logout, name= 'logout' )
]
