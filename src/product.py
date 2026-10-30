"""Pico Hello: the example Pico W product on App Base, and the starting point for new ones.

The base does the web page and API, the settings, MQTT and Home Assistant, Wi-Fi, setup mode, updates and the clock
(base/pico). This is what's Pico Hello's own: one setting, a greeting, shown on its page, on its MQTT state topic and
in Home Assistant, and changed from any of them.
"""
from base.settings import Setting, is_text
from version import VERSION  # noqa: F401  (scripts/wifi_update.py reads it there)

NAME = 'Pico Hello'
# The setup hotspot and the start of a name made from the board's id
SETUP_SSID = 'PicoHello-SETUP'
NAME_PREFIX = 'PicoHello-'
MANUFACTURER = 'Raspberry Pi'
MODEL = 'Pico W'

GREETING_LONGEST = 64

SETTINGS = {
    'hello': {
        'greeting': Setting('Hello from a Pico', is_text(GREETING_LONGEST, allow_empty=False)),
    },
}

# Home Assistant: the greeting, as a text box
HA_ENTITIES = (('text', 'greeting'),)


def info(device):
    return {'greeting': device.settings.get('hello', 'greeting')}


def state(device):
    """The state topic (<topic base>/state)."""
    return {'greeting': device.settings.get('hello', 'greeting')}


def set(device, command):
    """A command on the set topic (<topic base>/set): {"greeting": "..."}."""
    if any(key != 'greeting' for key in command):
        return 'only greeting can be set'
    error, changed = device.settings.update({'hello': command})
    if not error:
        device.applied(changed)
    return error


def applied(device, changed):
    # A new greeting from the page, the API or MQTT: the state topic says so
    if any(section == 'hello' for section, _ in changed):
        device.state_changed()


def ha_entity(device, key, t):
    return {'name': 'Greeting', 'icon': 'mdi:hand-wave', 'max': GREETING_LONGEST,
            'value_template': '{{ value_json.greeting }}',
            'command_topic': t['set'], 'command_template': '{"greeting": {{ value | tojson }}}'}
