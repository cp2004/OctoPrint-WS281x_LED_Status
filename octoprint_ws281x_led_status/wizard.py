from __future__ import absolute_import, division, unicode_literals

import io

from flask import jsonify

from octoprint_ws281x_led_status.util import run_system_command


def run_wizard_command(cmd, data, pi_model):
    command_to_system = {
        # -S for sudo commands means accept password from stdin, see https://www.sudo.ws/man/1.8.13/sudo.man.html#S
        'adduser': ['sudo', '-S', 'adduser', 'pi', 'gpio'],
        'enable_spi': ['sudo', '-S', 'bash', '-c', 'echo \'dtparam=spi=on\' >> /boot/config.txt'],
        'set_core_freq': ['sudo', '-S', 'bash', '-c',
                          'echo \'core_freq=500\' >> /boot/config.txt' if pi_model == '4' else 'echo \'core_freq=250\' >> /boot/config.txt'],
        'set_core_freq_min': ['sudo', '-S', 'bash', '-c',
                              'echo \'core_freq_min=500\' >> /boot/config.txt' if pi_model == '4' else 'echo \'core_freq_min=250\' >> /boot/config.txt'],
        'spi_buffer_increase': ['sudo', '-S', 'sed', '-i', '$ s/$/ spidev.bufsiz=32768/', '/boot/cmdline.txt']
    }
    validators = {
        'adduser': is_adduser_done,
        'enable_spi': is_spi_enabled,
        'set_core_freq': is_core_freq_set,
        'set_core_freq_min': is_core_freq_min_set,
        'spi_buffer_increase': is_spi_buffer_increased
    }
    if not validators[cmd](pi_model):
        stdout, error = run_system_command(command_to_system[cmd], data.get('password'))
    else:
        error = None
    return wizard_cmd_response(error)


def wizard_cmd_response(pi_model, errors=None):
    details = get_wizard_info(pi_model)
    details.update(errors=errors)
    return jsonify(details)


def get_wizard_info(pi_model):  # get_wizard_info to avoid any conflicts.
    return dict(
        adduser_done=is_adduser_done(pi_model),
        spi_enabled=is_spi_enabled(pi_model),
        spi_buffer_increase=is_spi_buffer_increased(pi_model),
        core_freq_set=is_core_freq_set(pi_model),
        core_freq_min_set=is_core_freq_min_set(pi_model)
    )


def is_adduser_done(pi_model):
    groups, error = run_system_command(['groups', 'pi'])
    return 'gpio' in groups


def is_spi_enabled(pi_model):
    with io.open('/boot/config.txt') as file:
        for line in file:
            if line.startswith('dtparam=spi=on'):
                return True
    return False


def is_spi_buffer_increased(pi_model):
    with io.open('/boot/cmdline.txt') as file:
        for line in file:
            if 'spidev.bufsiz=32768' in line:
                return True
    return False


def is_core_freq_set(pi_model):
    if int(pi_model) == 4:  # Pi 4's default is 500, which is compatible with SPI.
        return True  # any change to core_freq is ignored on a Pi 4, so let's not bother.
    with io.open('/boot/config.txt') as file:
        for line in file:
            if line.startswith('core_freq=250'):
                return True
    return False


def is_core_freq_min_set(pi_model):
    if int(pi_model) == 4:  # Pi 4 has a variable clock speed, which messes up SPI timing
        with io.open('/boot/config.txt') as file:  # This is only required on pi 4, not other models.
            for line in file:
                if line.startswith('core_freq_min=500'):
                    return True
        return False
    else:
        return True
