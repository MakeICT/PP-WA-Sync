import paypalrestsdk 
import logging
#logging.basicConfig(level=logging.INFO)

#See the paypal api docs for how to do this with environment 
#paypalrestsdk.configure({
  #"mode": "sandbox", # sandbox or live
  #"client_id": None,
  #"client_secret": None })


#IDs should be of the form I-xxxxxxxxxxxx for billing agreements. 
def get_billingAgreement_by_ID(pp_ID, debug = False):
	try:
		billing_agreement = BillingAgreement.find(str(pp_ID))
		if debug: 
			print("Got Billing Agreement Details for Billing Agreement[%s]" % (billing_agreement.id))
			print(billing_agreement)
		return(billing_agreement)
	except ResourceNotFound as error:
		if debug:
			print("Billing Agreement Not Found")
		return None

def get_transactions_by_BillingAgreement_ID(pp_ID, start_date="2010-01-01", end_date="2030-12-31" debug = False):
	try:
		billing_agreement = paypalrestsdk.BillingAgreement.find(pp_ID)
		transactions = billing_agreement.search_transactions(start_date, end_date)
		if debug:
			for transaction in transactions.agreement_transaction_list:
				print("  -> Transaction[%s]" % (transaction.transaction_id))
				print(transaction)
		return transactions

	except ResourceNotFound as error:
		print("Billing Agreement Not Found")
