import generalfunctions
import csv

#Setup to be redirectable to WA
subscription_ids_from_wa = generalfunctions.get_contact_and_subscription_ids(number=100, skip=200, debug=False,csv_out=False)

		
keys = subscription_ids_from_wa[0].keys()

#Compatible with the lookup_payments... which should NEVER find an unmatched one from this script, as it's reading from the audit log, which should record it. 
with open('reoccuring_payments.csv', 'w', encoding='utf8', newline='') as csvfile:
	writer = csv.DictWriter(csvfile, fieldnames=keys ) 
	writer.writeheader()
	writer.writerows(subscription_ids_from_wa)
	
