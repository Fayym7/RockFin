from django.contrib import admin
from .models import UserProfile, Loan, Payment, BillingCycle

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Loan)
admin.site.register(Payment)
admin.site.register(BillingCycle)