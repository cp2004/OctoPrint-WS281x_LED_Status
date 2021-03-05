/*
 * View model for OctoPrint-WS281x LED Status
 *
 * Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License
 */

const ko = window.ko;

$(function () {
    function ws281xLedStatusNavbarViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];

        self.torch_enabled = ko.observable(true);
        self.torch_toggle = ko.observable(true);

        var torch_on_src =
            "/plugin/ws281x_led_status/static/svg/flashlight.svg";
        var torch_off_src =
            "/plugin/ws281x_led_status/static/svg/flashlight-outline.svg";

        self.lights_on = ko.observable(true);
        self.torch_on = ko.observable(false);

        self.torch_icon = ko.observable(torch_off_src);

        function update_light_status(response) {
            if (response.lights_on) {
                self.lights_on(true);
            } else {
                self.lights_on(false);
            }
            if (response.torch_on) {
                self.torch_on(true);
                self.torch_icon(torch_on_src);
            } else {
                self.torch_on(false);
                self.torch_icon(torch_off_src);
            }
        }

        self.toggle_lights = function () {
            OctoPrint.simpleApiCommand(
                "ws281x_led_status",
                self.lights_on() ? "lights_off" : "lights_on"
            ).done(update_light_status);
        };

        self.toggle_torch = function () {
            if (self.torch_toggle()) {
                OctoPrint.simpleApiCommand(
                    "ws281x_led_status",
                    self.torch_on() ? "torch_off" : "torch_on"
                );
            } else {
                OctoPrint.simpleApiCommand(
                    "ws281x_led_status",
                    "torch_on"
                ).done(update_light_status);
            }
        };

        self.onBeforeBinding = function () {
            OctoPrint.simpleApiGet("ws281x_led_status").done(
                update_light_status
            );
            self.torch_enabled(
                self.settingsViewModel.settings.plugins.ws281x_led_status.effects.torch.enabled()
            );
            self.torch_toggle(
                self.settingsViewModel.settings.plugins.ws281x_led_status.effects.torch.toggle()
            );
        };

        self.onSettingsBeforeSave = function () {
            self.torch_enabled(
                self.settingsViewModel.settings.plugins.ws281x_led_status.effects.torch.enabled()
            );
            self.torch_toggle(
                self.settingsViewModel.settings.plugins.ws281x_led_status.effects.torch.toggle()
            );
        };

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "ws281x_led_status") {
                return;
            }
            if (data.type === "lights") {
                if (data.payload.on) {
                    self.lights_on(true);
                } else {
                    self.lights_on(false);
                }
            } else if (data.type === "torch") {
                if (data.payload.on) {
                    self.torch_on(true);
                    self.torch_icon(torch_on_src);
                } else {
                    self.torch_on(false);
                    self.torch_icon(torch_off_src);
                }
            }
        };

        // Tab change callback, if torch on webcam stream option enabled
        self.onAfterTabChange = function (current, previous) {
            if (
                current === "#control" &&
                self.settingsViewModel.settings.plugins.ws281x_led_status.effects.torch.enabled() &&
                self.settingsViewModel.settings.plugins.ws281x_led_status.effects.torch.toggle() &&
                self.settingsViewModel.settings.plugins.ws281x_led_status.effects.torch.auto_on_webcam() &&
                !self.torch_on()
            ) {
                // All relevant options are enabled, and the torch is currently off: make it on
                self.toggle_torch();
            } else if (
                previous === "#control" &&
                self.settingsViewModel.settings.plugins.ws281x_led_status.effects.torch.enabled() &&
                self.settingsViewModel.settings.plugins.ws281x_led_status.effects.torch.toggle() &&
                self.settingsViewModel.settings.plugins.ws281x_led_status.effects.torch.auto_on_webcam() &&
                self.torch_on()
            ) {
                // All relevant options are enabled, and the torch is on: make it off
                self.toggle_torch();
            }
        };
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: ws281xLedStatusNavbarViewModel,
        dependencies: ["settingsViewModel"],
        elements: ["#navbar_plugin_ws281x_led_status"],
    });

    function ws281xLedStatusSettingsViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];

        self.current_input = ko.observable(40);
        self.power_req = ko.observable("--W");
        self.power_req_12v = ko.observable("--W");
        self.current_req = ko.observable("--A");

        self.calculate_power = function () {
            var current_ma = parseInt(self.current_input(), 10);
            var num_pixels = parseInt(
                self.settingsViewModel.settings.plugins.ws281x_led_status.strip.count(),
                10
            );

            var current = (num_pixels * current_ma) / 1000;
            self.power_req((current * 5).toString(10) + "W");
            self.power_req_12v((current * 12).toString(10) + "W");
            self.current_req(current.toString(10) + "A");
        };

        self.sendTestCommand = function (color) {
            OctoPrint.simpleApiCommand("ws281x_led_status", "test_led", { color } );
        };

        self.advancedStripOpen = ko.observable(false);
        self.toggleAdvancedStrip = function () {
            $("#advancedStrip").collapse("toggle");
            self.advancedStripOpen(!self.advancedStripOpen());
        };
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: ws281xLedStatusSettingsViewModel,
        dependencies: ["settingsViewModel"],
        elements: [
            "#settings_plugin_ws281x_led_status",
            "#wizard_plugin_ws281x_led_status",
        ],
    });

    function ws281x_led_status_config_test_VM(parameters) {
        var self = this;
        /* Configuration testing */

        self.testInProgress = ko.observable(false);
        self.currentTest = ko.observable("");

        self.passwordForPi = ko.observable("");

        self.successfulTests = ko.observableArray();
        self.failedTests = ko.observableArray();

        self.test_id_map = {
            adduser: "User is in gpio group",
            spi_enabled: "SPI Enabled",
            spi_buffer_increase: "SPI buffer size increased",
            set_core_freq: "core_freq correct in /boot/config.txt",
            set_core_freq_min: "core_freq_min correct in /boot/config.txt",
        };
        self.reason_id_map = {
            failed: "This test did not pass",
            error:
                "Error: There was an unknown error running this test, please check the log",
            missing: "Error: The file this check expected does not exist",
            pi4_250:
                "It looks like core_freq_min=250 is set in your /boot/config.txt file." +
                " This needs to be removed manually for LEDs to work on a Pi 4.",
            not_required: "This is not required on your Raspberry Pi",
            "": "Test Passed",
        };
        self.test_id_to_command = {
            adduser: "wiz_adduser",
            spi_enabled: "wiz_enable_spi",
            spi_buffer_increase: "wiz_increase_buffer",
            set_core_freq: "wiz_set_core_freq",
            set_core_freq_min: "wiz_set_core_freq_min",
        };

        self.runConfigTest = function () {
            console.log("Starting ws281x_led_status OS configuration test");
            self.testInProgress(true);
            self.currentTest("");
            self.passwordForPi("");
            self.successfulTests([]);
            self.failedTests([]);

            OctoPrint.simpleApiCommand("ws281x_led_status", "test_os_config");
        };

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "ws281x_led_status") {
                return;
            }
            if (data.type === "os_config_test") {
                // Received data for the config test
                if (data.payload.status === "in_progress") {
                    self.currentTest(self.test_id_map[data.payload.test]);
                } else if (data.payload.status === "complete") {
                    self.testInProgress(false);
                } else if (data.payload.status.passed === true) {
                    self.successfulTests.push({
                        name: self.test_id_map[data.payload.test],
                        reason: self.reason_id_map[data.payload.status.reason],
                    });
                } else if (data.payload.status.passed === false) {
                    self.failedTests.push({
                        name: self.test_id_map[data.payload.test],
                        reason: self.reason_id_map[data.payload.status.reason],
                        fix_command: self.test_id_to_command[data.payload.test],
                        fixed: ko.observable(false),
                    });
                }
            }
        };

        self.runFixCommand = function (command, fixed) {
            var fixed_observable = fixed;
            OctoPrint.simpleApiCommand("ws281x_led_status", command, {
                password: self.passwordForPi(),
            }).done(function (response) {
                if (response.errors === "password") {
                    $("#cfgTestPasswordField").popover("show");
                } else {
                    fixed_observable(true);
                }
            });
        };

        self.passwdPopoverRemove = function () {
            $("#cfgTestPasswordField").popover("hide");
            return true;
        };
        self.onBeforeWizardFinish = function () {
            // Do not trigger notification if wizard is is not loaded
            if (!$("#wizard_plugin_ws281x_led_status").length) {
                return;
            }

            /* Trigger Pnotify dialog:
               if config incomplete, tell them it should be,
               if config complete, tell them to restart.
             */
            if (
                self.failedTests().length &&
                !(self.successfulTests().length === 5)
            ) {
                new PNotify({
                    title: "WS281X LED Status: Incomplete config",
                    text:
                        "Your configuration is not complete! Please head to the utilities tab in the settings page to fix this.",
                    type: "error",
                    hide: false,
                });
            } else {
                new PNotify({
                    title: "Restart needed!",
                    text:
                        "WS281x LED Status configuration complete. You will need to restart your Pi for the changes to take effect.",
                    type: "success",
                    hide: false,
                });
            }
        };
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: ws281x_led_status_config_test_VM,
        dependencies: [],
        elements: ["#WS_OS_CONFIG_TEST"],
    });
});
