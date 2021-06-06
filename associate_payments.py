"""associate_payments.py: Uses the database created by get_links.py. Runs through each entry and searches for 
                          profiles with payments within the past X days. If payments are found and the associated
                          WA user has an open membership invoice for that amount, a payment will be created in WA
                          and associated to that invoice. Processed payments are recorded in the SQLite database
                          to prevent duplication."""


import time
from datetime import datetime, timedelta

from paypalfunctions import get_billingAgreement_by_ID, get_transactions_by_BillingAgreement_ID

import generalfunctions
import database as db

test_mode = True
days = 3

start_date = (datetime.today()-timedelta(days=days)).date()
end_date = datetime.today().date()

result = db.session.query(db.Link).filter_by(ended=False)
active = result.count()
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
for row in result:
    print(row)
    agreement = get_billingAgreement_by_ID(row.recurring_id)
    # print(agreement.state)
    if agreement.state !="Active":
        # Mark the profile as ended in the local database so we can ignore it in the future
        active -= 1
        # print("INACTIVE AGREEMENT!!!")
        row.ended = True
        db.session.add(row)
        db.session.commit()
    else:
        # Get recent transactions for the active payment profile
        transactions = get_transactions_by_BillingAgreement_ID(row.recurring_id, start_date=start_date, end_date=end_date)
        # transactions = get_transactions_by_BillingAgreement_ID(row.recurring_id)
        try:
            for transaction in transactions['agreement_transaction_list']:
                print(transaction)
                if(db.session.query(db.Payment).get(transaction.transaction_id)):
                    print("Skipping previously processed payment")
                elif(transaction.status == 'Created' and not float(transaction.amount.value)):
                    print("Skipping profile creation transaction")
                else:    
                    contact_id = 38657966 if test_mode else row.wa_id

                    invoices = generalfunctions.get_invoices_by_contact_id(contact_id, unpaidOnly=True)
                    # invoices = generalfunctions.get_invoices_by_contact_id(row.wa_id, unpaidOnly=True)
                    print('------')
                    invoice_to_pay = None
                    for invoice in invoices.Invoices:
                        print(invoice.__dict__)
                        if invoice.Value == float(transaction.amount.value):
                            # invoice = generalfunctions.get_invoice(invoice.Id)
                            # print("####################")
                            # for item in invoice.__dict__:
                            #     print(item)
                            print(invoice.OrderType)
                            if invoice.OrderType == 'MembershipApplication' or invoice.OrderType == 'MembershipRenewal':
                                invoice_to_pay = invoice
                                break

                    if invoice_to_pay:
                        transaction_date = datetime.strptime(transaction.time_stamp, '%Y-%m-%dT%H:%M:%SZ')

                        wa_payment = generalfunctions.create_payment_for_contact_id(contact_id, amount=transaction.amount.value, 
                                                tenderId=506396, comment="PayPal_Transaction_ID: %s" % transaction.transaction_id,
                                                paydate=transaction_date)
                        result = generalfunctions.assign_payment_to_invoice(wa_payment.Id, invoice_to_pay.Id, transaction.amount.value)
                        new_payment = db.Payment(pp_transaction_id=transaction.transaction_id, wa_payment_id=wa_payment.Id)
                        print(f"Created WA payment {wa_payment.Id} from PP transaction {transaction.transaction_id} and applied it to WA invoice {invoice_to_pay.Id}")
                        db.session.add(new_payment)
                        db.session.commit()
                    else:
                        print("Couldn't find an invoice to pay with PP transaction {transaction.transaction_id}!")
                    exit()
        except KeyError:
            pass

print(active)
