from django.shortcuts import render, redirect
from datetime import datetime, timedelta
from django.contrib.auth.models import User,auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import UserProfile, Loan, Payment, Transaction, BillingCycle
from .tasks import calculate_credit_score
import json
from django.db.models import Sum
from django.db import transaction

def register_user_api(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        annual_income = request.POST.get('annual_income')
        aadhar_id = request.POST.get('aadhar_id')
        password = request.POST['password']
        password2 = request.POST['password2']
        
        if password==password2:
            if User.objects.filter(email=email).exists():
               messages.info(request,'Email taken')
               return redirect('signup')
            elif User.objects.filter(username=name).exists():
                messages.info(request,'Username Taken')
                return redirect('signup')
            else:
                user=User.objects.create_user(username=name,email=email,password=password)
                user.save()
                credit_score = calculate_credit_score.delay(aadhar_id)
                if credit_score == None:
                    messages.info(request,'Aadhar Entry not found in provided CSV file')
                    return redirect('signup')
                #log user in and redirect to settings page
                user_login= auth.authenticate(username=name,password=password)
                auth.login(request,user_login)

                #create a profile object for the new user

                user_model=User.objects.get(username=name)
                user_profile = UserProfile.objects.create(user= user, annual_income=annual_income, aadhar_id=aadhar_id, credit_score=credit_score) 
                user_profile.save()
                messages.info(request,'Account was created, Please login')
                return redirect('/')
                #log user in and redirect to settings page
                # user_login= auth.authenticate(username=username,password=password)
                # auth.login(request,user_login)
        # Create user profile
       
        else:
            messages.info(request,'Password not matching')
            return redirect('signup')

    else:
        return render(request,'signup.html')

def index(request):
        return render(request, 'index.html')
    
def signin(request):
    if request.method =='POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            print('logged in')
            return render(request, 'index.html', {'logged_in': True, 'user': user})
        else:
            messages.info(request, 'Invalid Credentials')
            return redirect('signin')

    else:
        return render(request, 'signin.html')

@login_required(login_url='signin')
def apply_loan_api(request):
    if request.method == 'POST':
        loan_amount = request.POST.get('loanAmount')
        interest_rate = 12
        term_period = request.POST.get('termPeriod')
        disbursement_date = datetime.today().date()
        # Validate user profile
        next_duedate = disbursement_date + timedelta(days=30)
        user_profile = UserProfile.objects.get(user= request.user)
        if (user_profile.credit_score < 450) or (user_profile.annual_income < 150000):
            return JsonResponse({'message':'Your credit score or income is below our eligibility criteria.'}, status = 400)

#####################################################################################
        apr = 12  # APR in percentage
        # apr_daily = round(apr / 100 / 365, 3)  # Calculate daily APR accrued
        # monthly_payment = (loan_amount * 0.03) + (apr_daily * 30 * loan_amount)
        # total_payment = monthly_payment * term_period
        print(term_period)
        term_period = int(term_period)
        loan_amount=int(loan_amount)
        monthly_interest_rate = float(apr / (12 * 100))  
        denominator = pow(1 + monthly_interest_rate, term_period) - 1 
        print(denominator)
        monthly_payment = (loan_amount * monthly_interest_rate * ((1 + monthly_interest_rate)**term_period))/ denominator
        total_payment = monthly_payment * term_period
#####################################################################################

        loan_object = Loan.objects.create(user= request.user, loan_amount= loan_amount, term_period=term_period,  disbursement_date= disbursement_date, loan_status='Pending', monthly_payment = monthly_payment, pending_amount = total_payment, next_duedate= next_duedate)
        loan_object.save()
        dates = []
        current_date = disbursement_date
        for _ in range(term_period):
            current_date += timedelta(days=30)
            dates.append(current_date.strftime("%Y-%m-%d"))

        print("Monthly Payment:", round(monthly_payment, 2))
        print("Total Payment:", round(total_payment, 2))
        return JsonResponse({'total_amount': total_payment, 'term_period': term_period, 'monthly_emi':monthly_payment, 'dates': dates }, status=200)
    else:
        return render(request, 'applyloan.html')


@login_required(login_url='signin')
def make_payment_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        amount = float(data.get('amount'))
        bill_id = data.get('bill_id')

        #############################################################
        try:
            with transaction.atomic():
                if bill_id == None:
                    loan = Loan.objects.filter(user = request.user, loan_status='Pending').first()
                    if loan == None:
                        return JsonResponse({'message': 'No Pending Loans to pay off'}, status=404)
                    
                    print(amount)
                    print(loan.pending_amount)
                    if float(loan.pending_amount) - amount < 0:
                        return JsonResponse({'message': f'Excess amount, Remaining amount for Loan ID {loan.loan_id} is Rs. {loan.pending_amount}'}, status= 200)
                    loan.pending_amount = float(loan.pending_amount) - amount
                    loan.term_period -= 1
                    loan.next_duedate += timedelta(days=30)
                    if loan.pending_amount == 0:
                        loan.term_period = 0 
                        loan.loan_status = 'Paid'
                    elif amount != loan.monthly_payment:
                        loan.monthly_payment = loan.pending_amount/loan.term_period  
                    loan.save()         
                else:      
                    loan = Loan.objects.get(bills__bill_id=bill_id)
                    bill = BillingCycle.objects.get(bill_id=bill_id)
                    loan.pending_amount = float(loan.pending_amount)-amount
                    loan.term_period -= 1
                    loan.next_duedate += timedelta(days=30)
                    if loan.pending_amount == 0:
                        loan.loan_status = 'Paid'
                    bill.pay_status='Paid'
                    bill.save()
                    loan.save() 
                payment_object = Payment.objects.create(loan= loan, amount= amount, payment_date= datetime.today().date())
                payment_object.save()
        except IntegrityError:
            # Transaction failed due to integrity error (e.g., unique constraint violation)
            return JsonResponse({'error': 'Transaction failed. Please try again.'}, status=500)
        
        return JsonResponse({'message': 'Amount was paid, Please Refresh to get updated Upcoming  payments'}, status=200)
    else:
        # pending_loans = Loan.objects.filter(user=request.user, loan_status='Pending').prefetch_related('bills').all()  # 'Pending' is the status for pending loans
        # pending_loans = Loan.objects.filter(user=request.user, loan_status='Pending').prefetch_related('bills')
        # Assuming there is a ForeignKey relationship between Bill and Loan models
        pending_loans = Loan.objects.filter(user = request.user, loan_status='Pending')
        for loan in pending_loans:
            bills = BillingCycle.objects.filter(loan__user=request.user, loan__loan_status='Pending', pay_status='Pending')
        bills = list(bills)
        print(bills)
        if pending_loans == None:
            context = {}
            return render(request, 'make_payment.html', context)
        pending_payments = []
        for loan in pending_loans:
            dates = []
            current_date = loan.next_duedate
            for _ in range(loan.term_period):
                dates.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=30)

            pending_payments.append((loan.disbursement_date, loan.monthly_payment, dates, loan.loan_id))

        context = {
            'repay': pending_payments,
            'past_billing_date': bills }

        return render(request, 'make_payment.html', context)    
        # return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required(login_url='signin')
def get_statement_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        loan_id = int(data.get('loan_id'))
        past_payments = Payment.objects.filter(loan__loan_id= loan_id)
        total_amount_paid = past_payments.aggregate(total_paid=Sum('amount'))['total_paid']
         # Check if total_amount_paid is None (no payments found)
        if total_amount_paid is None:
            total_amount_paid = 0
        print(loan_id)
        loan = Loan.objects.get(loan_id= loan_id)
        dates = []
        current_date = loan.next_duedate
        for _ in range(loan.term_period):
            dates.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=30)
        context = {
            'Date': loan.disbursement_date,
            'Principal': loan.loan_amount,
            'Interest': '12%',
            'Amount_Paid': total_amount_paid,
            'Upcoming_transactions':{'EMI_Dates': dates,
            'Amount_Due':loan.monthly_payment},
            
        }
        return JsonResponse(context, status=200)
        # Fetch transaction details
        # Calculate principal, interest, amount paid, and upcoming EMIs
        # Return response
    else:
        loans=Loan.objects.filter(user = request.user)
        context= {
            'loans':loans
        }
        return render(request, 'statements.html', context)

@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('/')
