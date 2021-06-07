"""associate_payments.py: Uses the database created by get_links.py. Runs through each entry and searches for 
                          profiles with payments within the past X days. If payments are found and the associated
                          WA user has an open membership invoice for that amount, a payment will be created in WA
                          and associated to that invoice. Processed payments are recorded in the SQLite database
                          to prevent duplication."""


import time
from datetime import datetime, timedelta
from math import fabs
import requests

from paypalfunctions import get_billingAgreement_by_ID, get_transactions_by_BillingAgreement_ID
import paypalrestsdk

import generalfunctions as gf
import database as db

test_mode = False
# test_mode = True
days = 7

start_date = (datetime.today()-timedelta(days=days)).date()
end_date = datetime.today().date()
print(start_date, end_date)

result = db.session.query(db.Link).filter_by(ended=False)
active = result.count()

if(test_mode):
    print("Script is running in test mode, so no changes will be made.")

def CheckInvoices(contact_id, value, transaction_date):
    invoices = gf.get_invoices_by_contact_id(contact_id, unpaidOnly=True)
    # invoices = gf.get_invoices_by_contact_id(contact_id, unpaidOnly=True)
    invoice_to_pay = None
    for invoice in invoices.Invoices:
        # for item in invoice.__dict__:
        #     print(item)
        # print(invoice.__dict__)
        if invoice.Value == float(value):
            invoice_date = datetime.strptime(invoice.CreatedDate, '%Y-%m-%dT%H:%M:%S')
            # print(transaction_date.date(), invoice_date.date())
            if abs((transaction_date.date() - invoice_date.date()).days) <= 9:
                # invoice = gf.get_invoice(invoice.Id)
                # print("####################")
                # print(invoice.OrderType)
                if invoice.OrderType == 'MembershipApplication' or invoice.OrderType == 'MembershipRenewal':
                    invoice_to_pay = invoice
                    return invoice

    print("Couldn't find invoice to pay!")
    return None
    

#TODO: Handle API connection issues: TimeoutError, 

count = 0
for row in result:
    # print(row)
    while True:
        try: 
            agreement = get_billingAgreement_by_ID(row.recurring_id)
            break
        except requests.exceptions.ConnectionError:
            print("Connection Error!")
            pass

    # print(agreement)
    if agreement.state !="Active":
        # Mark the profile as ended in the local database so we can ignore it in the future
        active -= 1
        # print("INACTIVE AGREEMENT!!!")
        row.ended = True
        db.session.add(row)
        db.session.commit()
    else:
        # Get recent transactions for the active payment profile
        got_transactions = False
        while not got_transactions:
            try:
                transactions = get_transactions_by_BillingAgreement_ID(row.recurring_id, start_date=start_date, end_date=end_date, debug=False)
                got_transactions = True
            except (requests.exceptions.ConnectionError, paypalrestsdk.exceptions.ServerError):
                print("Connection or Server Error!")
                time.sleep(10)
                pass
            
        # print(transactions)
        # transactions = get_transactions_by_BillingAgreement_ID(row.recurring_id)
        try:
            for transaction in transactions['agreement_transaction_list']:
                # print(transaction)
                transaction_date = datetime.strptime(transaction.time_stamp, '%Y-%m-%dT%H:%M:%SZ')
                
                if(db.session.query(db.Payment).get(transaction.transaction_id)):
                    print("Skipping previously processed payment")
                elif(transaction.status == 'Created' and not float(transaction.amount.value)):
                    print("Skipping profile creation transaction")
                else:    
                    print(count,'------',row.recurring_id, row.wa_id)
                    print(row)
                    contact_id = 38657966 if test_mode else row.wa_id
                    # contact_id = contact_id

                    result = gf.get_payments_by_contact_id(contact_id, transaction_date-timedelta(days=1), transaction_date+timedelta(days=1))
                    # result = gf.get_payments_by_contact_id(contact_id)
                    wa_payment = None
                    try:
                        if(result.Payments):
                            for payment in result.Payments:
                                # for thing in payment.__dict__:
                                #     print(thing)
                                # print('>>>')
                                print(payment.Id, payment.Value, transaction.amount.value)
                                print(fabs(payment.Value - float(transaction.amount.value)), payment.Comment)
                                if(fabs(payment.Value - float(transaction.amount.value)) <0.01):
                                    payment_date = gf.WADateToDateTime(payment.DocumentDate)
                                    print(payment_date.date(), transaction_date.date())
                                    if(payment_date.date() == transaction_date.date()):
                                        print("Payment found in Wild Apricot?")
                                        # wa_payment = payment
                                    else:
                                        print("Payment MAYBE found in Wild Apricot?")
                    except AttributeError as err:
                        print(">>>ERROR!", err)
                        pass
                    
                    wa_user = gf.get_contact_by_id(contact_id)
                    renewal_date = None
                    invoice_to_pay = None
                    new_renewal_date = datetime.strptime(agreement.agreement_details.next_billing_date, "%Y-%m-%dT%H:%M:%SZ")
                    res = CheckInvoices(contact_id, transaction.amount.value, transaction_date)
                    auto_update = True

                    if not res:
                        auto_update = False

                    for field in wa_user.FieldValues:
                        if field.SystemCode == "RenewalDue":
                            if field.Value:
                                renewal_date = datetime.strptime(field.Value, '%Y-%m-%dT%H:%M:%S')
                            else:
                                renewal_date = None
                                auto_update = False

                    if renewal_date:
                        if renewal_date > new_renewal_date + timedelta(days=7):
                            print("Current renewal date is further in the future than the next PP payment!")
                            print(wa_user.FirstName, wa_user.LastName)
                    else:
                        print("No renewal date!")
                        # continue

                    if not wa_payment:
                        pass
                        # print("Could not find payment in Wild Apricot!")
                    else:
                        print("Payment already exists in WA!")
                        continue

                    if wa_user.Status == "PendingRenewal":
                        print("PENDING!")
                    else:
                        auto_update = False
                        print(wa_user.Status)
                    
                    update = False
                    if not test_mode and not auto_update:
                    # if not test_mode and not auto_update:
                        print("\nManual approval required!")
                        print("-------------------------------------")
                        print(f"Status:\t\t\t{wa_user.Status}")
                        print(f"Renewal Date:\t\t{renewal_date}")
                        print(f"New Renewal Date:\t{new_renewal_date}")
                        print(f"Renewal Invoice:\t{res.Id if res else 'Not Found!'}")
                        print("-------------------------------------")

                        while True:
                            response = input(f"Modify user {wa_user.FirstName} {wa_user.LastName} : {contact_id} ?")
                            if response.lower().strip() == 'y':
                                update = True
                                break
                            elif response.lower().strip() == 'n':
                                break

                    if res:
                        invoice_to_pay = res
                    else:
                        if not test_mode and (update or auto_update):
                            print(f"Creating invoice...")
                            notes = f"Membership renewal. Level: {wa_user.MembershipLevel.Name}. Renew to {new_renewal_date}"
                            internal_notes = "Generated by python script"
                            gf.create_invoice(contact_id=contact_id, value=transaction.amount.value, created_by_id=None, 
                                        DocumentNumber = None, OrderType = 'MembershipRenewal', InternalMemo = internal_notes, 
                                        PublicMemo = '', Notes = notes, document_date=transaction_date )

                    res = CheckInvoices(contact_id, transaction.amount.value, transaction_date)
                    
                    if res:
                        invoice_to_pay = res
                    else:
                        print("Failed to create invoice!")
                        continue

                    if invoice_to_pay:
                        print(f"Identified PP transaction {transaction.transaction_id} which should apply to WA invoice {invoice_to_pay.Id}")
                    # else:                        
                        # wa_level = gf.get_membership_level(wa_user.MembershipLevel.Id)
                        # new_renewal_date = datetime.strptime(agreement.agreement_details.next_billing_date, "%Y-%m-%dT%H:%M:%SZ").date()

                    if not test_mode and (update or auto_update):
                        wa_payment = gf.create_payment_for_contact_id(contact_id, amount=transaction.amount.value, 
                            tenderId=506396, comment="PayPal_Transaction_ID: %s" % transaction.transaction_id,
                            paydate=transaction_date)
                        print(wa_payment.Id)
                        print(invoice_to_pay.Id)
                        result = gf.assign_payment_to_invoice(wa_payment.Id, invoice_to_pay.Id, transaction.amount.value)
                        gf.set_member_renewal_date(contact_id, new_renewal_date, "Active")
                        new_payment = db.Payment(pp_transaction_id=transaction.transaction_id, wa_payment_id=wa_payment.Id)
                        print(f"Created WA payment {wa_payment.Id} from PP transaction {transaction.transaction_id} and applied it to WA invoice {invoice_to_pay.Id}")
                        db.session.add(new_payment)
                        db.session.commit()
                    
                    print()
        except KeyError:
            print('KeyError')

    count += 1

print(active)
