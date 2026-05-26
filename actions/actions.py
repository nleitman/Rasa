
import os
import re
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
    
def _normalize_cancellation_target(value: Any) -> Text:
    """Normalize LLM-extracted cancellation targets.

    The LLM sometimes fills slot_cancellation_target with phrases like
    "my appointment" or even "I want to cancel my appointment". This helper
    strips filler words while preserving meaningful words like "internet",
    "premium", "order", and "appointment".
    """
    normalized = str(value or "").lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)

    filler_words = {
        "i",
        "want",
        "wanna",
        "would",
        "like",
        "need",
        "to",
        "please",
        "can",
        "you",
        "help",
        "me",
        "cancel",
        "cancelling",
        "cancellation",
        "stop",
        "my",
        "the",
        "a",
        "an",
        "this",
        "that",
        "for",
        "of",
    }

    words = [word for word in normalized.split() if word not in filler_words]
    return " ".join(words).strip()


def _specific_cancellation_terms(value: Any) -> Text:
    """Remove generic cancellation words while keeping the specific target.

    Examples:
      "subscription for internet" -> "internet"
      "gym membership" -> "gym"
      "premium membership" -> "premium"
      "monthly plan" -> "monthly"
      "subscription" -> "subscription"
    """
    normalized = _normalize_cancellation_target(value)

    generic_words = {
        "subscription",
        "membership",
        "service",
        "plan",
        "current",
        "for",
    }

    words = normalized.split()
    specific_words = [word for word in words if word not in generic_words]

    if specific_words:
        return " ".join(specific_words)

    return normalized


def _clear_cancellation_resolution() -> List[Dict[Text, Any]]:
    """Clear resolution slots and route back to clarification."""
    return [
        SlotSet("slot_cancellation_target", None),
        SlotSet("slot_cancellation_type", "needs_clarification"),
        SlotSet("selected_cancellable_item_id", None),
        SlotSet("slot_subscription_type", None),
        SlotSet("slot_cancellation_display_name", None),
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

        items = tracker.get_slot("available_cancellable_items") or []

        selected = tracker.get_slot("slot_cancellation_target")
        latest_text = (tracker.latest_message or {}).get("text")

        # Prefer the latest user answer over stale slot values.
        raw_target = latest_text or selected or ""
        selected_normalized = _normalize_cancellation_target(raw_target)

        logger.info(
            f"Resolving cancellation target. selected={selected!r}, "
            f"latest_text={latest_text!r}, raw_target={raw_target!r}, "
            f"normalized={selected_normalized!r}"
        )

        def needs_clarification_events():
            return [
                SlotSet("slot_cancellation_target", None),
                SlotSet("slot_cancellation_type", "needs_clarification"),
                SlotSet("selected_cancellable_item_id", None),
                SlotSet("slot_subscription_type", None),
                SlotSet("slot_cancellation_display_name", None),
            ]

        if not selected_normalized:
            return needs_clarification_events()

        generic_words = {
            "item", "specific", "something", "thing", "request",
            "cancellation", "subscription", "membership", "service",
            "plan", "current", "for", "of", "my",
        }

        user_tokens = set(selected_normalized.split())
        specific_tokens = {token for token in user_tokens if token not in generic_words}

        if not specific_tokens and selected_normalized in {
            "item", "specific item", "something", "thing", "request",
            "cancellation request", "subscription", "membership",
            "service", "plan", "current subscription",
            "my subscription", "my membership",
        }:
            logger.info("Cancellation target is vague; asking for clarification.")
            return needs_clarification_events()

        def normalized_item_name(item):
            return _normalize_cancellation_target(item.get("name", ""))

        def item_tokens(item):
            return set(normalized_item_name(item).split())

        def finish_match(matched):
            logger.info(f"Resolved cancellation target to: {matched}")

            events = [
                SlotSet("slot_cancellation_target", matched["name"]),
                SlotSet("slot_cancellation_type", matched["type"]),
                SlotSet("selected_cancellable_item_id", matched["id"]),
                SlotSet("slot_cancellation_display_name", matched["name"]),
            ]

            if matched["type"] == "subscription":
                events.append(SlotSet("slot_subscription_type", matched["name"]))
            else:
                events.append(SlotSet("slot_subscription_type", None))

            return events

        alias_to_item_name = {
            "gym": "gym membership",
            "gym membership": "gym membership",
            "internet": "internet service",
            "internet service": "internet service",
            "wifi": "internet service",
            "wi fi": "internet service",
            "meal": "meal kit service",
            "meal kit": "meal kit service",
            "meal kit service": "meal kit service",
            "box": "subscription box",
            "subscription box": "subscription box",
            "monthly": "monthly plan",
            "monthly plan": "monthly plan",
            "premium": "premium membership",
            "premium membership": "premium membership",
            "appt": "appointment on friday",
            "appointment": "appointment on friday",
            "friday": "appointment on friday",
            "appointment friday": "appointment on friday",
            "friday appointment": "appointment on friday",
            "visit": "appointment on friday",
            "session": "appointment on friday",
        }

        alias_target = alias_to_item_name.get(selected_normalized)

        if not alias_target and specific_tokens:
            specific_phrase = " ".join(
                token for token in selected_normalized.split()
                if token not in generic_words
            )
            alias_target = alias_to_item_name.get(specific_phrase)

        if alias_target:
            for item in items:
                if normalized_item_name(item) == alias_target:
                    return finish_match(item)

        if user_tokens & {"appointment", "appt", "friday", "visit", "session"}:
            appointment_matches = [
                item for item in items
                if str(item.get("type", "")).lower() == "appointment"
                or "appointment" in str(item.get("name", "")).lower()
            ]

            if len(appointment_matches) == 1:
                return finish_match(appointment_matches[0])

            return needs_clarification_events()

        digits = set(re.findall(r"\d+", selected_normalized))
        if "order" in user_tokens or digits:
            order_matches = [
                item for item in items
                if str(item.get("type", "")).lower() == "order"
            ]

            for item in order_matches:
                item_digits = set(re.findall(r"\d+", str(item.get("name", ""))))
                if digits and digits & item_digits:
                    return finish_match(item)

        scored = []

        for item in items:
            tokens = item_tokens(item)
            overlap = specific_tokens & tokens

            item_normalized = normalized_item_name(item)
            normalized_contains = (
                selected_normalized == item_normalized
                or selected_normalized in item_normalized
                or item_normalized in selected_normalized
            )

            score = len(overlap)

            if normalized_contains:
                score += 10

            if score > 0:
                scored.append((score, item))

        if not scored:
            logger.info("No cancellable item matched; asking for clarification.")
            return needs_clarification_events()

        scored.sort(key=lambda pair: pair[0], reverse=True)

        if len(scored) == 1 or scored[0][0] > scored[1][0]:
            return finish_match(scored[0][1])

        logger.info(f"Ambiguous cancellation target matches: {scored}")
        return needs_clarification_events()


class ActionContinueInterruptedFlow(Action):
    def name(self) -> Text:
        return "action_continue_interrupted_flow"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        logger.info("=== ENTERED action_continue_interrupted_flow ===")
        return []


class ActionPrepareCancellationConfirmation(Action):
    def name(self) -> Text:
        return "action_prepare_cancellation_confirmation"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        vague_targets = {
            "subscription",
            "membership",
            "service",
            "plan",
            "item",
            "something",
            "thing",
            "request",
            "cancellation request",
        }

        items = tracker.get_slot("available_cancellable_items") or []

        candidates = [
            tracker.get_slot("slot_cancellation_target"),
            tracker.get_slot("slot_subscription_type"),
        ]

        latest_text = (tracker.latest_message or {}).get("text")
        if latest_text:
            candidates.append(latest_text)

        display_name = None

        for value in candidates:
            normalized = _normalize_cancellation_target(value)
            if not normalized or normalized in vague_targets:
                continue

            # Prefer the clean item name from the available items list.
            for item in items:
                item_name = str(item.get("name", "")).strip()
                item_normalized = _normalize_cancellation_target(item_name)

                if (
                    normalized == item_normalized
                    or normalized in item_normalized
                    or item_normalized in normalized
                ):
                    display_name = item_name
                    break

            if display_name:
                break

            display_name = normalized
            break

        if not display_name:
            display_name = "this item"

        logger.info(f"Prepared cancellation display name: {display_name}")

        return [
            SlotSet("slot_cancellation_display_name", display_name),
            SlotSet("slot_from_cancel_flow", "Yes"),
            SlotSet("slot_confirmed", None),
            SlotSet("slot_user_wants_promo", None),
        ]
