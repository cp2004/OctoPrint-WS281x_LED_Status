/*
 * View model for OctoPrint-RGB LED Status
 *
 * Author: Charlie Powell
 * License: AGPLv3
 */
$(function() {
    function ws281xLEDStatusWizardViewModel(parameters) {
        var self = this;

        function runApiCommand(command) {
            console.log("command run")
            console.log(command)
            var password = $('#PasswordField').val();
            OctoPrint.simpleApiCommand('ws281x_led_status', command, {'password': password}).done(process_steps);
        }
        function process_steps(data) {
            if (data.errors === 'password') {
                $('#passwordIncorrect').removeClass('hidden').addClass('show')
            }
            else {
                $('#passwordIncorrect').removeClass('show').addClass('hidden')
            }
            if (data.adduser_done) {
                $('#addUser').addClass('text-success')
                $('#addUser i').removeClass('fa-arrow-right').addClass('fa-check')
                $('#addUserBtn').prop('disabled', true);
            }
            else {
                $('#addUserBtn').unbind('click').bind('click', function () {runApiCommand('adduser')});
            }
            if (data.spi_enabled) {
                $('#spiEnable').addClass('text-success')
                $('#spiEnable i').removeClass('fa-arrow-right').addClass('fa-check')
                $('#enableSPIBtn').prop('disabled', true)
            }
            else {
                $('#enableSPIBtn').unbind('click').bind('click', function () {runApiCommand('enable_spi')});
                $('#spiBufferIncrease').prop('disabled', true)
            }
            if (data.spi_buffer_increase) {
                $('#spiBufferIncrease').addClass('text-success')
                $('#spiBufferIncrease i').removeClass('fa-arrow-right').addClass('fa-check')
                $('#spiBufferIncreaseBtn').prop('disabled', true)
            }
            else {
                $('#spiBufferIncreaseBtn').unbind('click').bind('click', function () {runApiCommand('spi_buffer_increase')});
            }
            if (data.core_freq_set) {
                $('#coreFreqSet').addClass('text-success')
                $('#coreFreqSet i').removeClass('fa-arrow-right').addClass('fa-check')
                $('#coreFreqBtn').prop('disabled', true)
            }
            else {
                $('#coreFreqBtn').unbind('click').bind('click', function () {runApiCommand('set_core_freq')});
            }
            if (data.core_freq_min_set) {
                $('#coreFreqMinSet').addClass('text-success')
                $('#coreFreqMinSet i').removeClass('fa-arrow-right').addClass('fa-check')
                $('#coreFreqMinBtn').prop('disabled', true)
            }
            else {
                $('#coreFreqMinBtn').unbind('click').bind('click', function () {runApiCommand('set_core_freq_min')});
            }
        }
        self.name = "ws281xLEDStatusWiz"
        self.onWizardDetails = function (response) {
            process_steps(response.ws281x_led_status.details)
        };
        self.onBeforeWizardFinish = function () {
            return !$('#wizard_plugin_ws281x_led_status').find('ol li').not('.text-success').length;
        }
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: ws281xLEDStatusWizardViewModel,
        dependencies: ['wizardViewModel'],
        elements: ['#wizard_plugin_ws281x_led_status']
    });

    function ws281xLedStatusNavbarViewModel(parameters) {
        var self = this;
        var light_icon = $('#lightIcon')
        var switch_icon = $('#toggleSwitch')
        var timer_icon = $('#timerIndicator')

        function update_light_status(response) {
            if (response.lights_status) {
                light_icon.removeClass('far-custom text-error').addClass('fas-custom text-success')
                switch_icon.removeClass('fa-toggle-off text-error').addClass('fa-toggle-on text-success')
            } else {
                light_icon.removeClass('fas-custom text-success').addClass('far-custom text-error')
                switch_icon.removeClass('fa-toggle-on text-success').addClass('fa-toggle-off text-error')
            }
        }
        self.toggle_lights = function () {
            OctoPrint.simpleApiCommand('ws281x_led_status', 'toggle_lights').done(update_light_status)
        }

        self.onBeforeBinding = function () {
            OctoPrint.simpleApiGet('ws281x_led_status').done(update_light_status)
        }
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: ws281xLedStatusNavbarViewModel,
        elements: ['#navbar_plugin_ws281x_led_status']
    })
});

