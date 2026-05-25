import os
from typing import Any, Text, Dict, List

from dotenv import load_dotenv
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from twilio.rest import Client

load_dotenv()


class ActionSendSmsPromoText(Action):
    def name(self) -> Text:
        return "action_send_sms_promo_text"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:

        caller_number = tracker.get_slot("user_phone")

        # In rasa shell, user_phone is usually a random sender ID, not a real phone number.
        # Fall back to TEST_USER_PHONE from .env for local testing.
        if not caller_number or not (
            caller_number.startswith("+") or caller_number.startswith("whatsapp:+")
        ):
            caller_number = os.environ.get("TEST_USER_PHONE")

        if not caller_number:
            dispatcher.utter_message(
                text="I don't have a valid phone number to send the link to."
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
            to_number = caller_number

            # If the Twilio sender is WhatsApp, the recipient must also be WhatsApp.
            if twilio_number.startswith("whatsapp:") and not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"

            client = Client(account_sid, auth_token)
            client.messages.create(
                body=f"CSS: Here's the link to your subscription discount: {url}",
                from_=twilio_number,
                to=to_number,
            )

            dispatcher.utter_message(
                text="I've sent the link to your phone number."
            )

        except Exception:
            dispatcher.utter_message(
                text="Sorry, I was unable to send the SMS link."
            )

        return []
