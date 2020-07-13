/*
 * View model for OctoPrint-RGB LED Status
 *
 * Author: Charlie Powell
 * License: AGPLv3
 */
$(function() {
    function RGBLEDStatusWizardViewModel(parameters) {
        var self = this;

        function runApiCommand(command) {
            console.log("command run")
            console.log(command)
            var password = $('#PasswordField').val();
            OctoPrint.simpleApiCommand('rgb_led_status', command, {'password': password}).done(process_steps);
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
        self.name = "RGBLEDStatusWiz"
        self.onWizardDetails = function (response) {
            process_steps(response.rgb_led_status.details)
        };
        self.onBeforeWizardFinish = function () {
            return !$('#wizard_plugin_rgb_led_status').find('ol li').not('.text-success').length;
        }
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: RGBLEDStatusWizardViewModel,
        dependencies: ['wizardViewModel'],
        elements: ['#wizard_plugin_egb_led_status']
    });

    function Rgb_led_statusViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        // self.loginStateViewModel = parameters[0];
        // self.settingsViewModel = parameters[1];

        // TODO: Implement your plugin's view model here.
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: Rgb_led_statusViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ /* "loginStateViewModel", "settingsViewModel" */ ],
        // Elements to bind to, e.g. #settings_plugin_rgb_led_status, #tab_plugin_rgb_led_status, ...
        elements: [ /* ... */ ]
    });
});


