function getDropdownFromArray(array, id){
    var dropdown = `<select class="dorpdown" id="${id}">`;
    for (var i = 0; i < array.length; i++){
        dropdown += `<option value="${array[i]}">${array[i]}</option>`;
    }
    dropdown += "</select>";
    return dropdown;
}

function getInputField(id, type, placeholder){
    return `<input class="settings-input" type="${type}" id="${id}" placeholder="${placeholder}">`;
}

function getButton(id, text){
    return `<button class="settings-button" id="${id}">${text}</button>`;
}

async function loadSettings()
{
    const response = await fetch('/settings', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    const data = await response.json();
    if (data.settings) {
        return data.settings;
    }
}

function getSettingHTML(settings){
    var html = "<div class=settings>";
    if (settings.audio_settings) {
        html += "<div class=audio-settings>";
        html += "<h2>Audio Settings</h2>";
        if (settings.audio_settings.devices) {
            html += `Audio Device: ${getDropdownFromArray(settings.audio_settings.devices, "devices-dropdown")}`;
        }
        html += `<br>`;
        if (settings.audio_settings.channel1){
            html += `Channel 1: ${getInputField("channel1", "number", settings.audio_settings.channel1)}`;
        }
        if (settings.audio_settings.sine1_freq && settings.audio_settings.sine1_volume){
            html += `Test Sine Freq: ${getInputField("sine1_freq", "number", settings.audio_settings.sine1_freq)}`;
            html += `Volume: ${getInputField("sine1_freq", "number", settings.audio_settings.sine1_volume)}`;
            html += `${getButton("test-sine1", "Test")}`;
            html += `${getButton("test-sine1", "Stop")}`;
        }
        html += `<br>`;
        if (settings.audio_settings.channel2){
            html += `Channel 2: ${getInputField("channel2", "number", settings.audio_settings.channel2)}`;
        }
        if (settings.audio_settings.sine2_freq && settings.audio_settings.sine2_volume){
            html += `Test Sine Freq: ${getInputField("sine2_freq", "number", settings.audio_settings.sine2_freq)}`;
            html += `Volume: ${getInputField("sine2_freq", "number", settings.audio_settings.sine2_volume)}`;
            html += `${getButton("test-sine2", "Test")}`;
            html += `${getButton("test-sine2", "Stop")}`;
        }
        html += `<br>`;
        if (settings.audio_settings.channel3){
            html += `Channel 3: ${getInputField("channel3", "number", settings.audio_settings.channel3)}`;
        }
        if (settings.audio_settings.sine3_freq && settings.audio_settings.sine3_volume){
            html += `Test Sine Freq: ${getInputField("sine3_freq", "number", settings.audio_settings.sine3_freq)}`;
            html += `Volume: ${getInputField("sine3_freq", "number", settings.audio_settings.sine3_volume)}`;
            html += `${getButton("test-sine3", "Test")}`;
            html += `${getButton("test-sine3", "Stop")}`;
        }
        html += `<br>`;
        html += `${getButton("kill-all-test-sine", "Kill Test Sines")}`;
        html += "</div>";
        html += `<br>`;
    }
    if (settings.audio_model_settings) {
        html += "<div class=audio-model-settings>";
        html += "<h2>Audio Model Settings</h2>";
        html += "</div>";
        html += `<br>`;
    }
    if (settings.llm_model_settings) {
        html += "<div class=llm-model-settings>";
        html += "<h2>LLM Settings</h2>";
        html += "</div>";
        html += `<br>`;
    }
    if (settings.tracker_settings) {
        html += "<div class=tracker-settings>";
        html += "<h2>Tracker Settings</h2>";
        html += "</div>";
        html += `<br>`;
    }
    if (settings.headphone_sensors_settings) {
        html += "<div class=headphone-sensors-settings>";
        html += "<h2>Headphone Sensor Settings</h2>";
        html += "</div>";
    }
    html += "</div>";
    return html;
}

export { loadSettings, getSettingHTML};