
import os
import time
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted
#from twilio.rest import Client
import json
from datetime import datetime
from pathlib import Path


import logging

logger = logging.getLogger(__name__)

import logging
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted

logger = logging.getLogger(__name__)

class ActionSessionStart(Action):
    def name(self) -> str:
        return "action_session_start"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: dict
    ) -> list:

        logger.info("=== ENTERED custom action_session_start ===")
        logger.info(f"tracker.sender_id: {tracker.sender_id}")
        logger.info(f"session_started_metadata: {tracker.get_slot('session_started_metadata')}")
        logger.info(f"latest_message: {tracker.latest_message}")

        metadata = tracker.get_slot("session_started_metadata") or {}

        user_phone = metadata.get("user_phone") or tracker.sender_id
        bot_phone = metadata.get("bot_phone")

        logger.info(f"Setting user_phone to: {user_phone}")
        logger.info(f"Setting bot_phone to: {bot_phone}")

        return [
            SessionStarted(),
            SlotSet("user_phone", user_phone),
            SlotSet("bot_phone", bot_phone),
            ActionExecuted("action_listen"),
        ]

class ActionArtificialDelay(Action):
    def name(self) -> str:
        return "action_artificial_delay"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: dict) -> list:
        time.sleep(2)
        return []


ORDERED_DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def load_store_hours() -> Dict[Text, Any]:
    """
    Assumes this structure:

      project/
        actions/
          actions.py
        data/
          store_hours.json
    """
    project_root = Path(__file__).resolve().parent.parent
    file_path = project_root / "data" / "store_hours.json"

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def format_time(time_value: Text) -> Text:
    parsed_time = datetime.strptime(time_value, "%H:%M")
    return parsed_time.strftime("%I:%M %p").lstrip("0")


def format_day_hours(day: Text, hours: Dict[Text, Text]) -> Text:
    open_time = format_time(hours["open"])
    close_time = format_time(hours["close"])
    return f"{day.title()}: {open_time} - {close_time}"


class ActionGetAllStoreHours(Action):

    def name(self) -> Text:
        return "action_get_all_store_hours"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        store_data = load_store_hours()

        store_name = store_data.get("store_name", "The store")
        store_hours = store_data.get("hours", {})

        formatted_hours = [
            format_day_hours(day, store_hours[day])
            for day in ORDERED_DAYS
            if day in store_hours
        ]

        dispatcher.utter_message(
            text=f"{store_name} store hours are:\n" + "\n".join(formatted_hours)
        )

        return []


class ActionGetStoreHoursForDay(Action):

    def name(self) -> Text:
        return "action_get_store_hours_for_day"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        store_data = load_store_hours()

        store_name = store_data.get("store_name", "The store")
        store_hours = store_data.get("hours", {})

        requested_day = tracker.get_slot("slot_store_hours_day")

        if not requested_day:
            dispatcher.utter_message(
                text="I couldn't tell which day you wanted store hours for."
            )
            return []

        requested_day = requested_day.lower()

        if requested_day not in store_hours:
            dispatcher.utter_message(
                text=f"I couldn't find store hours for {requested_day.title()}."
            )
            return []

        formatted_hours = format_day_hours(requested_day, store_hours[requested_day])

        dispatcher.utter_message(
            text=f"{store_name} hours for {requested_day.title()} are {formatted_hours.split(': ', 1)[1]}."
        )

        return []
    
class ActionGetCancellableItems(Action):
    def name(self) -> Text:
        return "action_get_cancellable_items"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        user_phone = tracker.get_slot("user_phone")

        # Demo data. In production, look this up from CRM/billing/order system.
        items = [
            {"id": "sub_001", "name": "Gym membership", "type": "subscription"},
            {"id": "sub_002", "name": "Internet service", "type": "subscription"},
            {"id": "sub_003", "name": "Meal kit service", "type": "subscription"},
            {"id": "sub_004", "name": "Subscription box", "type": "subscription"},
            {"id": "sub_005", "name": "Monthly plan", "type": "subscription"},
            {"id": "sub_006", "name": "Premium membership", "type": "subscription"},
            {"id": "ord_123", "name": "Order 12345", "type": "order"},
            {"id": "appt_456", "name": "Appointment on Friday", "type": "appointment"},
        ]

        item_names = [item["name"] for item in items]
        item_text = ", ".join(item_names)

        return [
            SlotSet("available_cancellable_items", items),
            SlotSet("available_cancellable_items_text", item_text),
        ]
    
class ActionResolveCancellationTarget(Action):
    def name(self) -> Text:
        return "action_resolve_cancellation_target"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        selected = tracker.get_slot("slot_cancellation_target")
        items = tracker.get_slot("available_cancellable_items") or []

        if not selected:
            return [
                SlotSet("slot_cancellation_type", None),
                SlotSet("selected_cancellable_item_id", None),
                SlotSet("slot_subscription_type", None),
            ]

        selected_normalized = selected.lower().strip()

        # Do not treat vague wording as a real cancellable target.
        vague_targets = {
            "item",
            "specific item",
            "something",
            "thing",
            "entire subscription",
            "my subscription",
            "subscription",
            "membership",
            "service",
        }

        # These are subscription-like words, but if the user only says one of these,
        # we still want the bot to ask for the actual subscription/service.
        if selected_normalized in vague_targets:
            return [
                SlotSet("slot_cancellation_type", None),
                SlotSet("selected_cancellable_item_id", None),
                SlotSet("slot_subscription_type", None),
            ]

        # Aliases let natural descriptions resolve to demo items.
        aliases = {
            "gym": "gym membership",
            "gym membership": "gym membership",
            "internet": "internet service",
            "internet service": "internet service",
            "wifi": "internet service",
            "meal kit": "meal kit service",
            "meal kit service": "meal kit service",
            "subscription box": "subscription box",
            "monthly plan": "monthly plan",
            "premium membership": "premium membership",
        }

        normalized_target = aliases.get(selected_normalized, selected_normalized)

        matches = [
            item for item in items
            if item["name"].lower().strip() == normalized_target
            or normalized_target in item["name"].lower().strip()
            or item["name"].lower().strip() in normalized_target
        ]

        if not matches:
            return [
                SlotSet("slot_cancellation_type", None),
                SlotSet("selected_cancellable_item_id", None),
                SlotSet("slot_subscription_type", None),
            ]

        matched = matches[0]

        events = [
            SlotSet("slot_cancellation_target", matched["name"]),
            SlotSet("slot_cancellation_type", matched["type"]),
            SlotSet("selected_cancellable_item_id", matched["id"]),
        ]

        if matched["type"] == "subscription":
            events.append(SlotSet("slot_subscription_type", matched["name"]))

        return events