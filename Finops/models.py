from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

user=get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(user, on_delete=models.CASCADE)
    annual_income = models.DecimalField(max_digits=10, decimal_places=2)
    aadhar_id = models.CharField(max_length=12, unique=True)
    credit_score = models.IntegerField(default=0)  # Assuming credit score is an integer

    def __str__(self):
        return self.user.username


class Loan(models.Model):
    LOAN_STATUS = (('Pending', 'PENDING'),('Paid', 'PAID'))

    loan_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2)
    term_period = models.IntegerField()  # Duration for repayment in months
    disbursement_date = models.DateField()
    loan_status = models.CharField(max_length=10, choices= LOAN_STATUS)  # You can use choices for status
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2)
    next_duedate = models.DateField()
    def __str__(self): 
        return f"{self.user}'s Credit card Loan"

class BillingCycle(models.Model):
    PAY_STATUS = (('Pending', 'PENDING'),('Paid', 'PAID'))

    bill_id = models.AutoField(primary_key=True)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE , related_name='bills')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    billing_date = models.DateField()
    due_date = models.DateField()
    pay_status = models.CharField(max_length=10, choices= PAY_STATUS)
    amount_to_be_paid = models.DecimalField(max_digits=10, decimal_places=2)

class Payment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    # billing_cycle = models.OneToOneField(BillingCycle, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()

    def __str__(self):
        return f"Payment of {self.amount} for {self.loan}"


# NOT IN USE
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
    )

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    def __str__(self):
        return f"{self.transaction_type} Transaction of {self.amount} for {self.user} on {self.date}"
