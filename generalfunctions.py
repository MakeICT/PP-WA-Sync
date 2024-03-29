# -*- coding: utf-8 -*-

import logging
import json
import urllib.parse
from datetime import date, datetime, timedelta
import pytz
import time
#from WildApricotAPI import WaApiClient
#from WaApi import WaApiClient
import WaApi
#from dateutil import parser
import sys

api = None


def get_new_urls(): 
	global contactsUrl, eventsUrl, eventRegUrl, paymentAllocationUrl, paymentsUrl, invoicesUrl, tendersURL, auditLogURL, contactFieldsURL, membershipLevelsURL
	global api
	api = WaApi.WaApiClient('a','b')
	with open('wa-key', 'r') as keyFile:
		wildApricotKey = keyFile.read()
	api.authenticate_with_apikey(wildApricotKey) 
	accounts = api.execute_request('/v2.2/Accounts')
	account = accounts[0]
	for res in account.Resources: 
		# print (res)
		if res.Name == 'Contacts':
			contactsUrl = res.Url
		if res.Name == 'Events':
			eventsUrl = res.Url
		if res.Name == 'Event registrations':
			eventRegUrl = res.Url
		if res.Name == 'Payment allocations':
			paymentAllocationUrl = res.Url
		if res.Name == 'Payments':
			paymentsUrl = res.Url
		if res.Name == 'Invoices':
			invoicesUrl = res.Url
		if res.Name == 'Tenders':
			tendersURL = res.Url
		if res.Name == 'Audit log items':
			auditLogURL = res.Url
		if res.Name == 'Contact fields':
			contactFieldsURL = res.Url
		if res.Name == 'Membership levels':
			membershipLevelsURL = res.Url
	
	

def check_urls():
	if api is None:
		get_new_urls()
		
		

def assign_payment_to_invoice(payment_id, invoice_id, amount, debug = False):
	check_urls()
	if debug == True:
		print ("Assigning payment_id: " + str(payment_id) +' to invoice_id: ' + str(invoice_id) + ' of amount: ' + str(amount))
		
	request_url = paymentsUrl +  str(payment_id) + '/AllocateInvoice'
	api_request_object = { 'InvoiceId': invoice_id, 'Amount': amount}
	print(request_url)
	print(api_request_object)
	return api.execute_request(request_url, api_request_object=api_request_object, Printout=True, Test=False, method="POST")

def create_invoice(contact_id=0, value=0, created_by_id=0, DocumentNumber = '9999999', 
				   OrderType = 'Undefined', InternalMemo = 'TESTING', PublicMemo = 'TESTING PUBLIC MEMO', 
				   Notes = 'NOTE: TESTING IGNORE', document_date=None):
	# Verified, requires full admin token, not read only
	check_urls()
	#TODO: WTF is this for, James?
	# if DocumentNumber == '9999999':
	# 	#TODO handle this better
	# 	print("No Document Number Specified, Exiting")
	# 	exit(1)
	today = date.today()
	if not document_date:
		document_date = today.isoformat()
	Contact = { 'Id' : contact_id }
	OrderDetails = [{ 'Value' : value, 'OrderDetailType' : OrderType, 'Notes' : Notes }]
	params = {
		'Contact' : Contact,
		'DocumentDate': document_date.isoformat(), 
		'UpdatedDate': today.isoformat(), 
		'CreatedBy' : created_by_id,
		'UpdatedBy' : created_by_id,
		'Value' : value,
		# 'DocumentNumber' : DocumentNumber,
		'OrderType' : OrderType,
		'OrderDetails' : OrderDetails,
		'Memo' : InternalMemo,
		'PublicMemo' : PublicMemo
		}
	request_url = invoicesUrl 
	api_request_object = params
	return api.execute_request(request_url, api_request_object=api_request_object, Printout=True, Test=False, method="POST")


def get_unsettled_invoice_payments():
	check_urls()
	print('Getting unsettled payments')
	params = {'$top': '6000', '$async': 'false',  'unsettledOnly': 'true', 'PaymentType':'InvoicePayment'}
	request_url = paymentsUrl  + '?' + urllib.parse.urlencode(params)
	return api.execute_request(request_url, Printout=False)


def get_unsettled_payments():
	check_urls()
	print('Getting unsettled payments')
	params = {'$top': '600', '$async': 'false',  'unsettledOnly': 'true'}
	request_url = paymentsUrl  + '?' + urllib.parse.urlencode(params)
	return api.execute_request(request_url, Printout=False)


def get_payments_by_contact_id(contact_id, start_date=None, end_date=None):
	check_urls()

	params = {}

	params['ContactId'] = contact_id
	if start_date:
		start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
		params['StartDate'] = start_date_str
	if end_date:
		end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
		params['EndDate'] = end_date_str
	
	request_url = paymentsUrl + '?' + urllib.parse.urlencode(params)
	# print(request_url)

	return api.execute_request(request_url, Printout=False)


def get_invoice(invoice_id):
	check_urls()
	# print('Getting invoice')
	request_url = invoicesUrl + '/' + str(invoice_id)
	return api.execute_request(request_url, Printout=False)	


def get_invoices_unpaid():
	check_urls()
	print('Getting unpaid invoices')
	params = {'$top': '3', '$skip': '3', '$async': 'false', 'unpaidOnly': 'true' }#, 'contactId': str(WAID)}
	request_url = invoicesUrl + '?' + urllib.parse.urlencode(params)
	return api.execute_request(request_url, Printout=False)


def get_invoices_by_contact_id(WAID, unpaidOnly = False, debug = False):
	check_urls()
	if debug:
		print('Getting invoices for ID: ' + str(WAID))
	if unpaidOnly == False:
		params = {'$top': '10', '$async': 'false', 'contactId': str(WAID)}
	else:
		params = {'$top': '10', '$async': 'false', 'contactId': str(WAID), 'unpaidOnly': 'true' }
	request_url = invoicesUrl + '?' + urllib.parse.urlencode(params)
	return api.execute_request(request_url, Printout=False)


def get_payment_allocation_by_payment_id(WAID, debug = False):
	check_urls()
	if debug:
		print('Getting payments for ID: ' + str(WAID))
	params = {'$top': '10', '$async': 'false', 'paymentId': str(WAID)}
	request_url = paymentAllocationUrl + '?' + urllib.parse.urlencode(params)
	return api.execute_request(request_url, Printout=False)

def get_payment_allocation_by_contact_id(WAID, debug = False):
	check_urls()
	if debug:
		print('Getting payments for ID: ' + str(WAID))
	params = {'$top': '10', '$async': 'false', 'contactId': str(WAID)}
	request_url = paymentAllocationUrl + '?' + urllib.parse.urlencode(params)
	return api.execute_request(request_url, Printout=False)


# def get_payments_by_contact_id(WAID, unsettledOnly=False, debug = False):
# 	check_urls()
# 	if debug:
# 		print('Getting payments for ID: ' + str(WAID))
# 	if unsettledOnly == True:
# 		params = {'$top': '10', '$async': 'false', 'contactId': str(WAID), 'unsettledOnly': 'true'}
# 	else:
# 		params = {'$top': '10', '$async': 'false', 'contactId': str(WAID)}
# 	request_url = paymentsUrl + '?' + urllib.parse.urlencode(params)
# 	return api.execute_request(request_url, Printout=False)

def get_audit_log_by_id(WAID,debug=False):
	check_urls()
	if debug:
		print('Getting audit log  for ID: ' + str(WAID))
	params = {'$top': '10', '$async': 'false',  'itemId': str(WAID)}
	request_url = auditLogURL + '/' + str(WAID) + '?' + urllib.parse.urlencode(params)
#	print(request_url)
	return api.execute_request(request_url, Printout=debug)

def get_audit_log(number=10, debug=False, startdate=None, enddate=None, skip=0):
	check_urls()
	if debug:
		print('Getting Audit Log (ALL)')# for ID: ' + str(WAID))
	params = {'$top': '10', '$async': 'false'} #, 'contactId': str(WAID)}
	if startdate is None and enddate is None:
		today = date.today()
		threedays = timedelta(days=3000)
		shortcutoff = date.today() - threedays
		params = {'StartDate': shortcutoff.isoformat(),  'EndDate': today.isoformat(), '$async': 'false', '$top': number, '$skip': skip}
	else:
		params = {'StartDate': startdate.isoformat(),  'EndDate': enddate.isoformat(), '$async': 'false', '$top': number, '$skip': skip}
	request_url = auditLogURL + '?' + urllib.parse.urlencode(params)
	if debug:
		print(request_url)
	return api.execute_request(request_url, Printout=debug)

def get_contact_and_subscription_ids(number = 10, debug=False, csv_out=False, skip=0):
	output = []
	audit=get_audit_log(number = number, debug=debug, skip=skip)
	listing=audit.Items
	for items in listing:
		message = items.Message 
		if debug:
			print(message)
		#Not discarding yet, but it looks like there shouldn't be any use for this, as it should include a payment. 
		#if "PayPal Express Checkout subscription (recurring payment) created" in message:
			##Trim first part of message
			#paypal_subscription_id =  message.split("Subscription ID=",1)[1]
			##Trim trailing '.' from ID
			#paypal_subscription_id = paypal_subscription_id[:-1]
			#wildapricot_payer_id = items.Contact.Id
			#paypal_payer_fn = items.FirstName
			#paypal_payer_ln = items.LastName
			#paypal_payer_email = items.Email
			#payment_date = items.Timestamp
			##if debug or csv_out:
			#if debug:
				#print(str(paypal_payer_fn) + ',' + str(paypal_payer_ln) + ','+ str(paypal_payer_email) + ',' +str(wildapricot_payer_id) + ',' +str(paypal_subscription_id) )
			#output.append({'email': paypal_payer_email, 'firstname': paypal_payer_fn, 'lastname' :paypal_payer_ln, 'wildapricot_contact_id': wildapricot_payer_id, 'paypal_subscription_id': paypal_subscription_id, 'value' : -1, 'auditlogid' : items.Id, 'payment_date': payment_date})
		if "Payment received via PayPal Express Checkout. Amount " in message:
			recurring_payment_id = None
			amount = -1
			if debug:
				print('****')
			paypal_amount = message.split("Amount $", 1)[1]
			amount = float(paypal_amount[:-1])
			if debug: 
				print(amount)
			audit_log = get_audit_log_by_id(items.Id, debug=debug)
			audit_log_props = audit_log.Properties
			if debug:
				print('*****')
			if 'recurring_payment_id' in vars(audit_log_props).keys():
				recurring_payment_id = audit_log_props.recurring_payment_id
			if 'PROFILEID' in vars(audit_log_props).keys():
				recurring_payment_id = audit_log_props.PROFILEID
			
			if 'AMT' in vars(audit_log_props).keys():
				amounts = audit_log_props.AMT
				
			if 'amount' in vars(audit_log_props).keys():
				amounts = audit_log_props.amount
			
			pstcompdays = timedelta(hours=7)
			
			#Hate time formats
			if 'LASTPAYMENTDATE'  in vars(audit_log_props).keys():
				payment_date = audit_log_props.LASTPAYMENTDATE
				payment_date=payment_date[:-4] #All PST
				try: 
					paymentdate_good = datetime.strptime(payment_date, '%H:%M:%S %b %d, %Y')
					timezone = pytz.timezone('US/Pacific')
					paymentdate_good = timezone.localize(paymentdate_good)
				except ValueError as ex:
					#Because they have to be annoying some are Zulu time
					payment_date = audit_log_props.LASTPAYMENTDATE
					#paymentdate_good = datetime.fromisoformat(payment_date)
					paymentdate_good = datetime.strptime(payment_date, '%Y-%m-%dT%H:%M:%SZ')
					timezone = pytz.timezone('UTC')
					paymentdate_good = timezone.localize(paymentdate_good)
				
			if 'payment_date' in vars(audit_log_props).keys():
				payment_date = audit_log_props.payment_date
				payment_date=payment_date[:-4] #All PST
				try: 
					paymentdate_good = datetime.strptime(payment_date, '%H:%M:%S %b %d, %Y')
					timezone = pytz.timezone('US/Pacific')
					paymentdate_good = timezone.localize(paymentdate_good)
				except ValueError as ex:
					#Because they have to be annoying some are Zulu time
					payment_date = audit_log_props.payment_date
					paymentdate_good = datetime.strptime(payment_date, '%Y-%m-%dT%H:%M:%SZ')
					timezone = pytz.timezone('UTC')
					paymentdate_good = timezone.localize(paymentdate_good)
			paymentdate = paymentdate_good.isoformat()
			print(paymentdate)
			
			#For this we only care about the reoccurring payments
			if recurring_payment_id is not None:
				output.append({'email': audit_log.Email , 'firstname': audit_log.FirstName, 'lastname' : audit_log.LastName, 'wildapricot_contact_id': audit_log.Contact.Id, 'paypal_subscription_id': recurring_payment_id, 'amount' : amounts, 'auditlogid' : items.Id, 'paymentdate': paymentdate})
	return output

def get_contact_and_subscription_ids_2(number = 10, debug=False, skip=0):
	created = {}
	ended = {}
	audit=get_audit_log(number = number, debug=debug, skip=skip)
	listing=audit.Items
	for items in listing:
		message = items.Message
		recurring_payment_id = None
		# print(vars(items).keys()) 
		print(items.Timestamp)
		if debug:
			print(message)
		# if "PayPal Express Checkout subscription (recurring payment) ended" in message:
		# 	audit_log = get_audit_log_by_id(items.Id, debug=debug)
		# 	#TODO: audit logs before 2017 do not have any properties, but profile created/ended
		# 	#      messages have the profile ID in the message, so that could be used instead
		# 	audit_log_props = audit_log.Properties
		# 	if 'recurring_payment_id' in vars(audit_log_props).keys():
		# 		recurring_payment_id = audit_log_props.recurring_payment_id
		# 	if 'PROFILEID' in vars(audit_log_props).keys():
		# 		recurring_payment_id = audit_log_props.PROFILEID

		# 	if recurring_payment_id:
		# 		ended[recurring_payment_id] = audit_log.Contact.Id

		if "PayPal Express Checkout subscription (recurring payment) created" in message or \
				"Payment received via PayPal Express Checkout. Amount " in message:
			audit_log = get_audit_log_by_id(items.Id, debug=debug)
			audit_log_props = audit_log.Properties
			if 'recurring_payment_id' in vars(audit_log_props).keys():
				recurring_payment_id = audit_log_props.recurring_payment_id
				# print(audit_log_props.recurring_payment_id)
			if 'PROFILEID' in vars(audit_log_props).keys():
				recurring_payment_id = audit_log_props.PROFILEID

			if recurring_payment_id:
				created[recurring_payment_id] = audit_log.Contact.Id	
			return {"created":created,"ended":ended}

def get_membership_level(level_id):
	request_url = membershipLevelsURL + "/" + str(level_id)

	return api.execute_request(request_url)

def update_membership_level_by_id(WAID, LevelID, ReInvoice=False, debug = False):
	check_urls()
	params = {'contactId': str(WAID)}
	#Contact = [{ 'FieldName': 'Renewal due', 'Value' : set_to_date.isoformat(), 'SystemCode': 'RenewalDue' }]
	level = { 'Id' : LevelID } 
	if ReInvoice == False:
		updates = { 'Id' : WAID, 'MembershipLevel' : level , 'MembershipEnabled': 'true' } 
	else:
		updates = { 'Id' : WAID, 'MembershipLevel' : level , 'MembershipEnabled': 'true', 'RecreateInvoice': 'true'}
		updates = { 'Id' : WAID, 'RecreateInvoice': 'true'}
	request_url = contactsUrl  + str(WAID) #+   '?' + urllib.parse.urlencode(params)
	api_request_object = updates
	return api.execute_request(request_url, api_request_object=api_request_object, Printout=False, Test=False, method="PUT")

def set_member_renewal_date(wa_id, renewal_date, status=None, debug = False):
	# check_urls()
	request_url = contactsUrl  + str(wa_id)

	api_request_object = {
		'Id': wa_id,
		'FieldValues' : [
			{
			"SystemCode": "RenewalDue",
			"Value": DateTimeToWADate(renewal_date)
			}
		]
	}

	if status:
		api_request_object['Status'] = status
	return api.execute_request(request_url, api_request_object=api_request_object, Printout=False, Test=False, method="PUT")



def get_contact_by_id(WAID, debug = False):
	check_urls()
	if debug:
		print('Getting contacts for ID: ' + str(WAID))
	params = {'$top': '10', '$async': 'false', 'contactId': str(WAID)}
	request_url = contactsUrl + '/' + str(WAID) +   '?' + urllib.parse.urlencode(params)
	return api.execute_request(request_url, Printout=False)


def get_members_by_email_and_name(email, firstname, lastname, debug = False):
	check_urls()
	if debug:
		print("Finding contact/member for email " + str(email) + ' and name F/L: ' + str(firstname) + ' ' + str(lastname))
	params = {'$filter': 'substringof(\'Email\', \''+ email + '\') And \'LastName\' eq \'' + lastname  + '\'  And \'FirstName\' eq \'' + firstname +'\'', '$top': '20', '$async': 'false'}
	request_url = contactsUrl + '?' + urllib.parse.urlencode(params)
	return api.execute_request(request_url, Printout=False).Contacts

def get_contact_by_email(email, debug = False):
	check_urls()
	if debug:
		print("Finding contact/member for email " + str(email) + ' and name F/L: ' + str(firstname) + ' ' + str(lastname))
	params = {'$filter': 'substringof(\'Email\', \''+ email + '\')', '$top': '20', '$async': 'false'}
	request_url = contactsUrl + '?' + urllib.parse.urlencode(params)
	return api.execute_request(request_url, Printout=False).Contacts

def create_payment_for_contact_id(contact_id, amount, tenderId=None, paytype='Unknown', comment= 'Auto-Generated-TEST', paydate=None, debug = False):
	check_urls()
	if debug:
		print ('Creating payment for contact ID: ' + str(WAID) + ' of amount: ' + str(amount) + ' and type: ' + str(paytype))
	if paydate is None:
		paydate = datetime.today()
	Contacts = { 'Id' : contact_id }
	params = {
		'Contact' : Contacts,
		'Value' : amount, 
		'PaymentType' : paytype,
		'Tender': {'Id': tenderId},
		'DocumentDate' : paydate.isoformat(),
		'Comment': comment,
		# 'Invoices': [{'Id':23071}],
	}
	request_url = paymentsUrl 
	api_request_object = params
	if debug:
		print(request_url)
		print(api_request_object)
	return api.execute_request(request_url, api_request_object=api_request_object, Printout=False, Test=False, method="POST")
		

def WADateToDateTime(wa_date):
	fixed_date = wa_date[0:22]+wa_date[23:]
	try:
		py_date = datetime.strptime(fixed_date, '%Y-%m-%dT%H:%M:%S%z')
	except ValueError:
		py_date = datetime.strptime(fixed_date, '%Y-%m-%dT%H:%M:%S')

	return py_date

def DateTimeToWADate(py_date):
	try:
		if not py_date.tzinfo==None:
			utc = pytz.timezone("UTC")
			py_date = py_date.astimezone(utc)
	except AttributeError:
		pass

	return py_date.strftime('%Y-%m-%dT%H:%M:%S')