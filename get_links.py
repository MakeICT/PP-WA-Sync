"""get_links.py: Parses WA audit logs to get associations between PayPal recurring profile Ids
                 and WA user IDs. These links are saved to an SQLite database."""


import time

from paypalfunctions import get_billingAgreement_by_ID, get_transactions_by_BillingAgreement_ID

import generalfunctions
import database as db

number=100
skip=0

created = {} 
ended = {}
empty_results = 0

consecutive_errors = 0
keep_going = True
search_done = False

current_status = None 
last_status = db.session.query(db.Status).order_by(db.Status.id.desc()).limit(1).first()

if last_status and not last_status.complete:
    print("Resuming last session")
    skip = last_status.skip
    skip = 60000
    current_status = last_status
else:
    print("Starting new session")
    current_status = db.Status(skip=0)
    db.session.add(current_status)
    db.session.commit()

while(run):
    try:
        subscription_ids_from_wa = generalfunctions.get_contact_and_subscription_ids_2(number=number, skip=skip, debug=False,csv_out=False)
        consecutive_errors = 0
        # run = False
    except OSError as err:
        print("OS error: {0}".format(err))
        # if isinstance(err, HTTPResponse) and err.code == 500:
        #     break
        consecutive_errors += 1
        time.sleep(10 * consecutive_errors)
        if consecutive_errors > 5:
            break
        else:
            continue

    except KeyboardInterrupt:
        print("Exiting due to keyboard interrupt!")
        break

    if not subscription_ids_from_wa['created'] and not subscription_ids_from_wa['ended']:
        empty_results += 1
        if empty_results > 10:
            search_done = True
            break

    # print(subscription_ids_from_wa)

    for profile in subscription_ids_from_wa['created']:
        created[profile] = subscription_ids_from_wa['created'][profile]

    for profile in subscription_ids_from_wa['ended']:
        ended[profile] = subscription_ids_from_wa['ended'][profile]

    print("created:",len(created))
    print("ended:",len(ended))

    skip += number
    print(skip)

# status = db.Status(skip=skip, complete=search_done)
current_status.skip = skip
current_status.complete = search_done
db.session.add(current_status)
db.session.commit()

for profile in created:
    if not db.session.query(db.Link).get(profile):
        new_link = db.Link(recurring_id=profile, wa_id = created[profile])
        db.session.add(new_link)
        print("new link:",new_link)
    else:
        print("link already exists!")
    
    db.session.commit()

    
for profile in ended:
    existing_link = db.session.query(db.Link).get(profile)
    if existing_link:
        existing_link.ended = True
        db.session.add(existing_link)
        print("ended existing link:", existing_link)
    else:
        new_link = db.Link(recurring_id=profile, wa_id = ended[profile], ended=True)
        db.session.add(new_link)
        print("new ended link:", new_link)
    db.session.commit()

# Quick and dirty way to restart script after WA token times out and fails to refresh
import os, sys
os.execv(__file__, sys.argv)
