
from celery import shared_task
from django.conf import settings
import csv
from .models import UserProfile, Loan, Payment, Transaction, BillingCycle
from datetime import datetime, timedelta
import os

@shared_task
def create_billing_cycle():
    loans = Loan.objects.filter(loan_status = 'Pending')
    for loan in loans:
        if loan.next_duedate == datetime.today().date():
            bill = BillingCycle.objects.create(loan= loan, user= loan.user, billing_date=loan.next_duedate, due_date= (loan.next_duedate + timedelta(days=15)), pay_status ='Pending', amount_to_be_paid= loan.monthly_amount )
            bill.save()

@shared_task
def calculate_credit_score(target_user):
    total_debit = 0
    total_credit = 0
    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'csvfile', 'transactions_data_backend__1_.csv')
    try:
        with open(csv_file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                user = row['user']
                if user == target_user:
                    amount = float(row['amount'])
                    transaction_type = row['transaction_type']
                    if transaction_type == 'DEBIT':
                        total_debit += amount
                    elif transaction_type == 'CREDIT':
                        total_credit += amount
    except (FileNotFoundError, csv.Error) as e:
        # Handle file-related errors
        print(f"Error: {e}")
        return None

    balance = total_credit - total_debit
    if balance >= 1000000:
            credit_score = 900
    elif balance <= 100000:
        credit_score = 300
    else:
        credit_score = 300 + ((balance - 100000) // 15000) * 10
        credit_score = min(900, credit_score)

    return credit_score