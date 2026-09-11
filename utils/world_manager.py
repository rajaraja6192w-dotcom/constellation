"""World system manager - handles weather, events, time periods, and world state"""

import json
import os
import random
import time
from datetime import datetime, timezone
from typing import Dict, Tuple

# Load world config with correct path
_current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_world_config_path = os.path.join(_current_dir, "data", "world_config.json")

with open(_world_config_path, "r", encoding="utf-8") as f:
    WORLD_CONFIG = json.load(f)

WEATHER_TYPES = WORLD_CONFIG["weather_types"]
EVENT_TYPES = WORLD_CONFIG["event_types"]
TIME_PERIODS = WORLD_CONFIG["time_periods"]
NULL_POTION_DROP = WORLD_CONFIG["null_potion_drop"]

def get_current_utc_time() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)

def get_time_period() -> Tuple[str, Dict]:
    """Get current time period (Night or Morning) based on UTC hour."""
    current_hour = get_current_utc_time().hour
    
    for period_name, period_data in TIME_PERIODS.items():
        if current_hour in period_data["hours"]:
            return period_name, period_data
    
    # Fallback to Morning
    return "Morning", TIME_PERIODS["Morning"]

def should_regenerate_world(world_state: dict) -> bool:
    """Check if world state should be regenerated (every 6 hours)."""
    import logging
    
    if not world_state or "last_update" not in world_state:
        logging.info("🌍 World state doesn't exist or missing last_update - regenerating")
        return True
    
    current_time = time.time()
    last_update = world_state["last_update"]
    time_diff = current_time - last_update
    
    # Regenerate every 6 hours (21600 seconds)
    should_regen = time_diff >= 21600
    
    if should_regen:
        logging.info(f"🌍 World regeneration triggered - {time_diff/3600:.2f} hours since last update")
    else:
        hours_remaining = (21600 - time_diff) / 3600
        logging.info(f"🌍 World state valid - {hours_remaining:.2f} hours until next regeneration")
    
    return should_regen

def generate_weather() -> Tuple[str, Dict]:
    """Randomly generate weather based on chances."""
    rand = random.random()
    cumulative = 0.0
    
    for weather_name, weather_data in WEATHER_TYPES.items():
        cumulative += weather_data["chance"]
        if rand <= cumulative:
            return weather_name, weather_data
    
    # Fallback to Sunny
    return "Sunny", WEATHER_TYPES["Sunny"]

def generate_event() -> Tuple[str, Dict]:
    """Randomly generate event based on chances."""
    rand = random.random()
    cumulative = 0.0
    
    for event_name, event_data in EVENT_TYPES.items():
        cumulative += event_data["chance"]
        if rand <= cumulative:
            return event_name, event_data
    
    # Fallback to Normal
    return "Normal", EVENT_TYPES["Normal"]

def initialize_world_state() -> dict:
    """Generate new world state."""
    weather_name, weather_data = generate_weather()
    event_name, event_data = generate_event()
    time_period, time_data = get_time_period()
    
    world_state = {
        "last_update": time.time(),
        "weather": {
            "name": weather_name,
            "icon": weather_data["icon"],
            "luck_bonus": weather_data["luck_bonus"],
            "description": weather_data["description"]
        },
        "event": {
            "name": event_name,
            "icon": event_data["icon"],
            "luck_bonus": event_data["luck_bonus"],
            "description": event_data["description"],
            "special_effects": event_data.get("special_effects", [])
        },
        "time_period": {
            "name": time_period,
            "icon": time_data["icon"],
            "description": time_data["description"],
            "exclusive_lights": time_data.get("exclusive_lights", []),
            "exclusive_boost": time_data.get("exclusive_boost", 0)
        }
    }
    
    return world_state

def get_world_state(db_state: dict = None) -> dict:
    """Get or generate world state."""
    import logging
    
    if db_state and not should_regenerate_world(db_state):
        # Update time period dynamically (changes hourly)
        time_period, time_data = get_time_period()
        
        # Check if time period changed
        if db_state["time_period"]["name"] != time_period:
            logging.info(f"🌍 Time period changed: {db_state['time_period']['name']} → {time_period}")
        
        db_state["time_period"] = {
            "name": time_period,
            "icon": time_data["icon"],
            "description": time_data["description"],
            "exclusive_lights": time_data.get("exclusive_lights", []),
            "exclusive_boost": time_data.get("exclusive_boost", 0)
        }
        return db_state
    
    # Generate new world state
    logging.info("🌍 Generating NEW world state (weather + event)")
    return initialize_world_state()

def calculate_world_luck_bonus(world_state: dict) -> float:
    """Calculate total luck bonus from world state (as percentage)."""
    weather_bonus = world_state["weather"]["luck_bonus"]
    event_bonus = world_state["event"]["luck_bonus"]
    
    # Total bonus as percentage
    return weather_bonus + event_bonus

def get_world_display(world_state: dict) -> str:
    """Format world state for display."""
    import time
    
    # Get current UTC time with explicit timezone
    utc_now = get_current_utc_time()
    time_str = utc_now.strftime("%H:%M:%S")
    date_str = utc_now.strftime("%Y-%m-%d")
    
    weather = world_state["weather"]
    event = world_state["event"]
    time_period = world_state["time_period"]
    
    total_luck = calculate_world_luck_bonus(world_state)
    
    # Calculate time until next regeneration
    last_update = world_state.get("last_update", time.time())
    time_since = time.time() - last_update
    time_until_regen = 21600 - time_since  # 6 hours in seconds
    
    if time_until_regen > 0:
        hours = int(time_until_regen // 3600)
        minutes = int((time_until_regen % 3600) // 60)
        regen_str = f"{hours}h {minutes}m"
    else:
        regen_str = "Soon!"
    
    text = "🌍 <b>WORLD STATE</b> 🌍\n"
    text += "="*35 + "\n\n"
    
    # Time - with explicit UTC label
    text += f"🕐 <b>UTC Time:</b> {time_str} UTC\n"
    text += f"📅 <b>Date:</b> {date_str}\n"
    text += f"⏰ <b>Next Regen:</b> {regen_str}\n"
    text += f"{time_period['icon']} <b>Period:</b> {time_period['name']}\n"
    if time_period['exclusive_lights']:
        exclusive = ", ".join(time_period['exclusive_lights'])
        text += f"   └ <i>Exclusive: {exclusive} (+{time_period['exclusive_boost']}%)</i>\n"
    text += "\n"
    
    # Weather
    text += f"{weather['icon']} <b>Weather:</b> {weather['name']}\n"
    text += f"   └ <i>{weather['description']}</i>\n"
    text += f"   └ Luck: +{weather['luck_bonus']}%\n\n"
    
    # Event
    text += f"{event['icon']} <b>Event:</b> {event['name']}\n"
    text += f"   └ <i>{event['description']}</i>\n"
    text += f"   └ Luck: +{event['luck_bonus']}%\n"
    
    # Special effects
    if event['special_effects']:
        text += "   └ <b>Special Effects:</b>\n"
        for effect in event['special_effects']:
            if isinstance(effect, dict):
                text += f"      • {effect.get('description', 'Unknown effect')}\n"
            elif effect == "eclipse_light_unlock":
                text += "      • 🌔 Eclipse light is obtainable!\n"
    
    text += "\n"
    text += f"✨ <b>TOTAL WORLD LUCK BONUS: +{total_luck}%</b>\n"
    text += "="*35
    
    return text

def check_null_potion_drop() -> bool:
    """Check if Null Potion drops (0.1% chance)."""
    return random.random() <= NULL_POTION_DROP["chance"]

def check_burnt_effect(world_state: dict) -> bool:
    """Check if player gets Burnt effect during Meteor Fall event."""
    if world_state["event"]["name"] != "Meteor Fall":
        return False
    
    # Find burnt effect in special effects
    for effect in world_state["event"]["special_effects"]:
        if isinstance(effect, dict) and effect.get("type") == "burnt_effect":
            return random.random() <= effect["chance"]
    
    return False

def is_eclipse_active(world_state: dict) -> bool:
    """Check if Eclipse event is active."""
    return world_state["event"]["name"] == "Eclipse"

def get_meteorite_boost(world_state: dict) -> float:
    """Get Meteorite chance multiplier if Meteor Fall event active."""
    if world_state["event"]["name"] != "Meteor Fall":
        return 1.0
    
    # Find meteorite boost in special effects
    for effect in world_state["event"]["special_effects"]:
        if isinstance(effect, dict) and effect.get("type") == "meteorite_boost":
            return effect.get("multiplier", 1.0)
    
    return 1.0

def check_anomaly_from_none_event(world_state: dict) -> bool:
    """Check if Anomaly can be obtained from None event (5% chance)."""
    if world_state["event"]["name"] != "None":
        return False
    
    # Find anomaly chance in special effects
    for effect in world_state["event"]["special_effects"]:
        if isinstance(effect, dict) and effect.get("type") == "anomaly_chance":
            return random.random() <= effect["chance"]
    
    return False

def is_light_available(light_name: str, world_state: dict) -> bool:
    """Check if a light is available based on time period."""
    time_period = world_state["time_period"]
    exclusive_lights = time_period.get("exclusive_lights", [])
    
    # If no exclusive lights, all lights available
    if not exclusive_lights:
        return True
    
    # Check if this light is time-exclusive
    if light_name in ["Sunrise", "Moonlight"]:
        return light_name in exclusive_lights
    
    # Non-exclusive lights are always available
    return True

def get_time_exclusive_boost(light_name: str, world_state: dict) -> float:
    """Get luck boost for time-exclusive lights."""
    time_period = world_state["time_period"]
    exclusive_lights = time_period.get("exclusive_lights", [])
    
    if light_name in exclusive_lights:
        return time_period.get("exclusive_boost", 0) / 100.0
    
    return 0.0

def is_heaven_approach_active(world_state: dict) -> bool:
    """Check if Heaven Approach event is active."""
    return world_state["event"]["name"] == "Heaven Approach"

def is_poseidon_fury_active(world_state: dict) -> bool:
    """Check if Poseidon Fury event is active."""
    return world_state["event"]["name"] == "Poseidon Fury"

def check_exclusive_light_drop(world_state: dict, user_data: dict) -> bool:
    """Check if exclusive light can drop during Heaven Approach (15% chance, Pro only).
    
    Args:
        world_state: Current world state
        user_data: User data dict
    
    Returns:
        bool: True if exclusive light should drop
    """
    # Must be Heaven Approach event
    if not is_heaven_approach_active(world_state):
        return False
    
    # Must have Pro tier
    from database import has_exclusive_light_access
    if not has_exclusive_light_access(user_data):
        return False
    
    # Find exclusive light chance in special effects
    for effect in world_state["event"]["special_effects"]:
        if isinstance(effect, dict) and effect.get("type") == "exclusive_light_chance":
            return random.random() <= effect["chance"]
    
    return False
