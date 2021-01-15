/*
 * View model for OctoPrint-WS281x LED Status
 *
 * Author: Charlie Powell
 * License: AGPLv3
 */

const ko = window.ko;

$(function () {
    function ws281xLEDStatusWizardViewModel(parameters) {
        var self = this;

        self.passwordForPi = ko.observable("");
        self.addUserDone = ko.observable(false);
        self.inProgressAddUser = ko.observable(false);
        self.enabledSPI = ko.observable(false);
        self.inProgressEnableSPI = ko.observable(false);
        self.spiBufferIncreased = ko.observable(false);
        self.inProgressSpiBuffer = ko.observable(false);
        self.coreFreqSet = ko.observable(false);
        self.inProgressCoreFreq = ko.observable(false);
        self.coreFreqMinSet = ko.observable(false);
        self.inProgressCoreFreqMin = ko.observable(false);

        self.passwdPopoverRemove = function () {
            $("#wizardPasswordField").popover("hide");
        };

        self.runApiCommand = function (command) {
            OctoPrint.simpleApiCommand("ws281x_led_status", command, {
                password: self.passwordForPi(),
            }).done(self.check_config);
        };

        self.runAddUser = function () {
            self.inProgressAddUser(true);
            self.runApiCommand("wiz_adduser");
        };
        self.runEnableSPI = function () {
            self.inProgressEnableSPI(true);
            self.runApiCommand("wiz_enable_spi");
        };
        self.runIncreaseSPIBuffer = function () {
            self.inProgressSpiBuffer(true);
            self.runApiCommand("wiz_increase_buffer");
        };
        self.runSetCoreFreq = function () {
            self.inProgressCoreFreq(true);
            self.runApiCommand("wiz_set_core_freq");
        };
        self.runSetCoreFreqMin = function () {
            self.inProgressCoreFreqMin(true);
            self.runApiCommand("wiz_set_core_freq_min");
        };

        self.check_config = function (response) {
            if (response.errors === "password") {
                $("#wizardPasswordField").popover("show");
            } else {
                $("#wizardPasswordField").popover("hide");
            }
            if (response.adduser_done) {
                self.addUserDone(true);
            } else {
                self.addUserDone(false);
            }
            if (response.spi_enabled) {
                self.enabledSPI(true);
            } else {
                self.enabledSPI(false);
            }
            if (response.spi_buffer_increase) {
                self.spiBufferIncreased(true);
            } else {
                self.spiBufferIncreased(false);
            }
            if (response.core_freq_set) {
                self.coreFreqSet(true);
            } else {
                self.coreFreqSet(false);
            }
            if (response.core_freq_min_set) {
                self.coreFreqMinSet(true);
            } else {
                self.coreFreqMinSet(false);
            }
            // Set all request spinners to false
            self.inProgressAddUser(false);
            self.inProgressEnableSPI(false);
            self.inProgressSpiBuffer(false);
            self.inProgressCoreFreq(false);
            self.inProgressCoreFreqMin(false);
        };
        self.onWizardDetails = function (response) {
            self.check_config(response.ws281x_led_status.details);
        };
        self.onBeforeWizardFinish = function () {
            /* Trigger Pnotify dialog:
               if config incomplete, tell them it should be,
               if config complete, tell them to restart.
             */
            if (
                !self.addUserDone() ||
                !self.enabledSPI() ||
                !self.spiBufferIncreased() ||
                !self.coreFreqSet() ||
                !self.coreFreqMinSet()
            ) {
                new PNotify({
                    title: "WS281X LED Status: Incomplete config",
                    text:
                        "Your configuration is not complete! please head to the utilities tab in the settings page to fix this!",
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
        construct: ws281xLEDStatusWizardViewModel,
        dependencies: ["wizardViewModel"],
        elements: ["#wizard_plugin_ws281x_led_status"],
    });

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
                if (data.on) {
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
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: ws281xLedStatusNavbarViewModel,
        dependencies: ["settingsViewModel"],
        elements: ["#navbar_plugin_ws281x_led_status"],
    });

    function ws281xLedStatusSettingsViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];

        var current_input = $("#currentInput_mA");

        $("#calc_btn").bind("click", function () {
            calculate_power();
        });

        function calculate_power() {
            var current_ma = parseInt(current_input.val(), 10);
            var num_pixels = parseInt($("#ws281x_num_leds").val(), 10);

            var current = (num_pixels * current_ma) / 1000;
            var power = current * 5;
            update_vals(power, current);
        }
        function update_vals(power, current) {
            $("#power_req").text(power + "W");
            $("#current_req").text(current + "A");
        }

        /* LED Test buttons - TODO swap to SimpleAPI calls - see #39 */

        $("#led-test-red").bind("click", function () {
            send_m150(255, 0, 0);
        });
        $("#led-test-green").bind("click", function () {
            send_m150(0, 255, 0);
        });
        $("#led-test-blue").bind("click", function () {
            send_m150(0, 0, 255);
        });
        $("#led-test-white").bind("click", function () {
            send_m150(255, 255, 255);
        });

        function send_m150(r, g, b) {
            var command = "M150 R" + r + " G" + g + " B" + b;
            OctoPrint.control.sendGcode(command);
        }
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: ws281xLedStatusSettingsViewModel,
        dependencies: ["settingsViewModel"],
        elements: "#settings_plugin_ws281x_led_status",
    });

    function ws281x_led_status_config_test_VM(parametera) {
        var self = this;
        /* Configuration testing */

        self.testInProgress = ko.observable(false);
        self.currentTest = ko.observable("");
        self.testSuccess = ko.observable(false);
        self.testFailures = ko.observable(false);

        self.passwordForPi = ko.observable("");

        self.addUserStatus = ko.observable("");
        self.spiEnabledStatus = ko.observable("");
        self.spiBufferStatus = ko.observable("");
        self.coreFreqStatus = ko.observable("");
        self.coreFreqMinStatus = ko.observable("");

        self.runConfigTest = function () {
            console.log("Starting ws281x_led_status OS configuration test");
            self.testInProgress(true);
            self.testSuccess(false);
            self.testFailures(false);

            self.passwordForPi("");

            self.addUserStatus("");
            self.spiEnabledStatus("");
            self.spiBufferStatus("");
            self.coreFreqStatus("");
            self.coreFreqMinStatus("");

            OctoPrint.simpleApiCommand("ws281x_led_status", "test_os_config");
        };

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "ws281x_led_status") {
                return;
            }
            if (data.type === "os_config_test") {
                // Received data for the config test
                if (data.payload.status === "in_progress") {
                    if (data.payload.test === "adduser") {
                        self.currentTest("User pi in gpio group");
                    } else if (data.payload.test === "spi_enabled") {
                        self.currentTest("SPI enabled");
                    } else if (data.payload.test === "spi_buffer_increase") {
                        self.currentTest("SPI Buffer size increased");
                    } else if (data.payload.test === "set_core_freq") {
                        self.currentTest("core_freq set in /boot/config.txt");
                    } else if (data.payload.test === "set_core_freq_min") {
                        self.currentTest(
                            "core_freq_min set in /boot/config.txt"
                        );
                    }
                } else {
                    if (data.payload.test === "adduser") {
                        self.addUserStatus(data.payload.status);
                    } else if (data.payload.test === "spi_enabled") {
                        self.spiEnabledStatus(data.payload.status);
                    } else if (data.payload.test === "spi_buffer_increase") {
                        self.spiBufferStatus(data.payload.status);
                    } else if (data.payload.test === "set_core_freq") {
                        self.coreFreqStatus(data.payload.status);
                    } else if (data.payload.test === "set_core_freq_min") {
                        self.coreFreqMinStatus(data.payload.status);
                    } else if (data.payload.test === "complete") {
                        if (!self.testFailures()) {
                            self.testSuccess(true);
                        }
                        self.testInProgress(false);
                    }
                }
                // if any tests fail, this will tell the user to do something & show password
                if (data.payload.status === "failed") {
                    self.testFailures(true);
                }
            }
        };

        self.fixAddUser = function () {
            OctoPrint.simpleApiCommand("ws281x_led_status", "adduser", {
                password: self.passwordForPi(),
            }).done(self.processApiCmdResponse);
        };
        self.fixEnableSpi = function () {
            OctoPrint.simpleApiCommand("ws281x_led_status", "enable_spi", {
                password: self.passwordForPi(),
            }).done(self.processApiCmdResponse);
        };
        self.fixIncreaseSpiBuffer = function () {
            OctoPrint.simpleApiCommand(
                "ws281x_led_status",
                "spi_buffer_increase",
                { password: self.passwordForPi() }
            ).done(self.processApiCmdResponse);
        };
        self.fixCoreFreq = function () {
            OctoPrint.simpleApiCommand("ws281x_led_status", "set_core_freq", {
                password: self.passwordForPi(),
            }).done(self.processApiCmdResponse);
        };
        self.fixCoreFreqMin = function () {
            OctoPrint.simpleApiCommand(
                "ws281x_led_status",
                "set_core_freq_min",
                { password: self.passwordForPi() }
            ).done(self.processApiCmdResponse);
        };

        self.processApiCmdResponse = function (response) {
            if (response.errors === "password") {
                $("#cfgTestPasswordField").popover("show");
            }
            if (response.adduser_done) {
                self.addUserStatus("passed");
            }
            if (response.spi_enabled) {
                self.spiEnabledStatus("passed");
            }
            if (response.spi_buffer_increase) {
                self.spiBufferStatus("passed");
            }
            if (response.core_freq_set) {
                self.coreFreqStatus("passed");
            }
            if (response.core_freq_min_set) {
                self.coreFreqMinStatus("passed");
            }
        };
        self.passwdPopoverRemove = function () {
            $("#cfgTestPasswordField").popover("hide");
            return true;
        };
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: ws281x_led_status_config_test_VM,
        dependencies: [],
        elements: ["#generic_plugin_ws281x_led_status"],
    });
});
