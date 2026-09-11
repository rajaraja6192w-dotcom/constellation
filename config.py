"""Configuration file for Constellation RNG Bot"""

import json
import os

# Bot Configuration
BOT_TOKEN = "8768449848:AAG-QNkVtMXybzQ6SKcGiwOE-8HJlBK3pbs"
MAX_INVENTORY_SLOTS = 120

# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Load lights from JSON
def load_lights():
    """Load lights from lights.json"""
    lights_file = os.path.join(DATA_DIR, "lights.json")
    with open(lights_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['lights'], data['special_lights'], data.get('exclusive_lights', [])

# Load gears from JSON
def load_gears():
    """Load gears from gears.json"""
    gears_file = os.path.join(DATA_DIR, "gears.json")
    with open(gears_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['gears']

# Load potions from JSON
def load_potions():
    """Load potions from potions.json"""
    potions_file = os.path.join(DATA_DIR, "potions.json")
    with open(potions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['potions']

# Load achievements from JSON
def load_achievements():
    """Load achievements from achievements.json"""
    achievements_file = os.path.join(DATA_DIR, "achievements.json")
    with open(achievements_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['achievements']

# Load daily quests from JSON
def load_daily_quests():
    """Load daily quests from daily_quests.json"""
    quests_file = os.path.join(DATA_DIR, "daily_quests.json")
    with open(quests_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# Initialize data
LIGHTS, SPECIAL_LIGHTS, EXCLUSIVE_LIGHTS = load_lights()
GEARS = load_gears()
POTIONS = load_potions()
ACHIEVEMENTS = load_achievements()
DAILY_QUESTS_DATA = load_daily_quests()

# Debug: Print loaded data
print(f"✅ Config loaded: {len(LIGHTS)} lights, {len(GEARS)} gears, {len(POTIONS)} potions")
print(f"✅ Gear names: {list(GEARS.keys())}")
