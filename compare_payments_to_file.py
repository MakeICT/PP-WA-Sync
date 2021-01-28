import generalfunctions #Interface to WA
import csv
import datetime
#import pytz # Timezone because WTF PYTHON?!

'''
CSV FILE FORMAT: 

firstname, lastname, email, paymentdate, amount

paymentdate in iso format WITH timezone
Ex: 2021-01-01T00:00:01+06:00

'''

debug=False
hours_delta=13

with open('reoccuring_payments.csv') as csvfile:
	reader = csv.DictReader(csvfile, delimiter=',',skipinitialspace=True ) 
	result = []
	for row in reader:
		result.append(row)
	if debug:
		print(result)


any_unmatched = False
for item in result:
	if debug:
		print(item)
	contacts = generalfunctions.get_members_by_email_and_name(item['email'], item['firstname'], item['lastname'], debug = debug)
	date_object = datetime.datetime.fromisoformat(item['paymentdate'])
	if len(contacts) == 1:
		contact = contacts[0]
		if debug:
			print (contact.Id)
		payments = generalfunctions.get_payments_by_contact_id(contact.Id)
		payments_list=[]
		matched = False
		for payment in payments:
			if debug:
				print(str(payment.CreatedDate) + ', ' + str(payment.Value))
			if payment.Tender is not None:
				if payment.Tender.Id == 6:
					if debug:
						print("PayPal Recurring Payment")
				else:
					if debug:
						print ('NON Paypal payment')
			if payment.Tender is None:
				if debug:
					print ('Unknown payment type!')
			payments_list.append({ 'Value' : payment.Value, 'Date': payment.DocumentDate, 'Id': payment.Id})
			#print(payments_list)
			if float(payment.Value) == float(item['amount']):
				#matched = True
				if debug:
					print("MATCHING PAYMENT AMOUNT")
				paydate_object = datetime.datetime.fromisoformat(payment.DocumentDate)
				margin = datetime.timedelta(hours=hours_delta)
				if paydate_object + margin > date_object and paydate_object - margin < date_object:
					matched = True
				if debug: 
					if paydate_object + margin > date_object and paydate_object - margin < date_object:
						print("MATCHING DATE")
					else:
						print("MATCHING DATE: FAILED *************")
						print(paydate_object.isoformat())
						print(date_object.isoformat())
					print(str(payment.Value) + ' at '+ str(payment.DocumentDate) + ' for ' + str(contact.DisplayName))
					print("MATCHING PAYMENT")
			else:
				if debug:
					print("Not matched: ")
					print(payment.Value)
					print(item['amount'])
		if matched is False:
			any_unmatched = True
			print('*****')
			print('No matching payments for:')
			print(str(contact.DisplayName) + ' for the amount of ' + str(item['amount']) + ' at ' + date_object.isoformat())
			#print('creating one with input') 
			xyzzy = input("Press Y then Enter to create payment: ")
			if xyzzy == 'Y':
				print("Creating")
				generalfunctions.create_payment_for_contact_id(contact.Id, item['amount'], paydate=date_object)
			else:
				print("Input was not 'Y', NOT creating payment")
			print('*****')
	else:
		print('Number of matching contacts: ' + str(len(contacts)))
		print('Skipping')
		#exit(1)
		
		
# Just so it doesn't exit with no output
if any_unmatched is False:
	print("All payments in file, matched")
