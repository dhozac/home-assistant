"""Script to print requirements for configured components."""
import argparse
import logging
import os

from typing import List

import voluptuous as vol

import homeassistant.bootstrap as bootstrap
import homeassistant.config as conf_util
import homeassistant.loader as loader
import homeassistant.core as core

_LOGGER = logging.getLogger(__name__)


# pylint: disable=too-many-locals, too-many-branches
def run(script_args: List) -> int:
    """Handle print requirements commandline script."""
    parser = argparse.ArgumentParser(
        description=("Print Home Assistant requirements."))
    parser.add_argument(
        '--script', choices=['print_reqs'])
    parser.add_argument(
        '-c', '--config',
        default=conf_util.get_default_config_dir(),
        help="Directory that contains the Home Assistant configuration")

    args = parser.parse_args()

    config_dir = os.path.join(os.getcwd(), args.config)
    config_path = os.path.join(config_dir, 'configuration.yaml')
    if not os.path.isfile(config_path):
        print('Config does not exist:', config_path)
        return 1

    logging.basicConfig(level=logging.ERROR)

    try:
        hass = core.HomeAssistant()
        if config_dir is not None:
            config_dir = os.path.abspath(config_dir)
            hass.config.config_dir = config_dir
        config = conf_util.load_yaml_config_file(config_path)
        core_config = config.get(core.DOMAIN, {})
        try:
            conf_util.async_process_ha_core_config(hass, core_config)
        except vol.Invalid as ex:
            bootstrap.log_exception(ex, 'homeassistant', core_config)
            return 1

        conf_util.process_ha_config_upgrade(hass)
    except Exception as err:  # pylint: disable=broad-except
        print('Fatal error while loading config:', str(err))
        return 1

    loader.prepare(hass)
    components = set(key.split(' ')[0] for key in config.keys()
                     if key != core.DOMAIN)
    for domain in loader.load_order_components(components):
        component = loader.get_component(domain)
        for req in getattr(component, 'REQUIREMENTS', []):
            print(req)

    return 0
