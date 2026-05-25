
import os
import time
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
#from twilio.rest import Client
import json
from datetime import datetime
from pathlib import Path


from twilio.rest import Client
from rasa_sdk.types import DomainDict

class ActionSendSmsPromoText(Action):
    def name(self) -> Text:
        return "action_send_sms_promo_text"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> List[Dict[Text, Any]]:

        caller_number = tracker.get_slot("user_phone")

        if not caller_number:
            dispatcher.utter_message(
                text="I don't have a phone number to send the SMS to."
            )
            return []

        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")

        if not account_sid or not auth_token or not twilio_number:
            dispatcher.utter_message(
                text="Twilio is not configured correctly."
            )
            return []

        url = "https://rasa.com"

        try:
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=f"CSS: Here's the link to your subscription discount: {url}",
                from_=twilio_number,
                to=caller_number
            )

            dispatcher.utter_message(
                text="I've sent the link to your phone number."
            )

        except Exception:
            dispatcher.utter_message(
                text="Sorry, I was unable to send the SMS link."
            )

        return []
    