"""Pico Hello's own part, with App Base's real settings (saved in a temporary folder), topics and discovery."""
import json
import os
import types

import pytest

import product
from base import discovery, mqtt, pico
from base.device import Device

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def device(tmp_path):
    platform = types.SimpleNamespace(state_path=lambda name: str(tmp_path / name), device_name=lambda: 'hello',
                                     NAME_EDITABLE=True, health=lambda: {}, SENSORS=())
    d = Device(product, platform)
    d.states = 0

    def state_changed():
        d.states += 1
    d.state_changed = state_changed
    return d


def test_the_greeting_starts_as_the_default(device):
    assert product.state(device) == {'greeting': 'Hello from a Pico'}
    assert product.info(device) == {'greeting': 'Hello from a Pico'}


def test_a_greeting_from_mqtt_is_saved_and_its_state_sent(device, tmp_path):
    assert product.set(device, {'greeting': 'Morning'}) is None
    assert product.state(device) == {'greeting': 'Morning'}
    assert device.states == 1
    assert json.loads((tmp_path / 'config.json').read_text())['hello']['greeting'] == 'Morning'


@pytest.mark.parametrize('command', [{'greeting': ''}, {'greeting': 'x' * 65}, {'greeting': 5}, {'colour': 'red'}])
def test_a_wrong_command_is_refused_and_changes_nothing(device, command):
    assert product.set(device, command)
    assert product.state(device) == {'greeting': 'Hello from a Pico'}
    assert device.states == 0


def test_home_assistant_gets_a_text_box_on_the_set_topic():
    t = mqtt.topics('hello', sensors=pico.SENSORS, product_state=True, entities=product.HA_ENTITIES)
    config = json.loads(discovery.entity('hello', t, product, 'greeting', product.ha_entity(None, 'greeting', t)))
    assert config['command_topic'] == 'home/device/hello/set'
    assert config['state_topic'] == 'home/device/hello/state'
    assert config['max'] == product.GREETING_LONGEST
    assert config['device']['sw_version'] == product.VERSION


def test_the_example_config_has_the_products_settings_and_their_defaults():
    with open(os.path.join(ROOT, 'config.example.json'), encoding='utf-8') as f:
        example = json.load(f)
    for section, settings in product.SETTINGS.items():
        assert example[section] == {key: setting.default for key, setting in settings.items()}
