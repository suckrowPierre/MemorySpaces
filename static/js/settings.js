let changes = {};

async function loadSettings(fromDisk=false) {
    var path = fromDisk ? '/settings/disk' : '/settings';
    const response = await fetch(path, { method: 'GET', headers: { 'Content-Type': 'application/json' } });
    const data = await response.json();
    return data.settings || {};
}

async function saveSettings() {
    const response = await fetch('/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(changes),
    });
    const data = await response.json();
    if (data.success) {
        alert("Settings saved successfully");
    } else {
        alert("Error saving settings");
    }
    changes = {};
}




function initializeSettingsListeners() {
    document.querySelectorAll('.settings-input, .settings-dropdown').forEach(element => {
        const originalValue = element.value;
        element.addEventListener('change', (event) => {
            console.log("change", element.id, event.target.value);
            const [section, setting] = element.id.split('-');
            if (!changes[section]) {
                changes[section] = {};
            }
            if (event.target.value !== originalValue) {
                changes[section][setting] = element.value;
            } else {
                delete changes[section][setting];
                if (Object.keys(changes[section]).length === 0) {
                    delete changes[section];
                }
            }
            console.log("changes", changes);
        });
    });
}




function getSettingHTML(settings) {
    return `<div class="settings">
        ${createButton("start-programm", "Start Programm") + createButton("save-settings", "Save Settings") + createButton("load-settings-from-disk", "Load Settings from Disk")}
        ${createSettingsSection(settings, "audio_settings", createAudioSettingsContent)}
        ${createSettingsSection(settings, "audio_model_settings", createAudioModelSettingsContent)}
        ${createSettingsSection(settings, "llm_settings", createLLMSettingsContent)}
        ${createSettingsSection(settings, "tracker_settings", () => '')}
        ${createSettingsSection(settings, "headphone_sensors_settings", () => '')}
    </div>`;
}

function createAudioSettingsContent(audioSettings) {
    let content = '';
    if (audioSettings.device_options) {
        // check if device is in options
        if(!audioSettings.device_options.includes(audioSettings.device) || audioSettings.device == ""){
            if (!changes["audio_settings"]) {
                changes["audio_settings"] = {};
            }
            audioSettings.device = audioSettings.device_options[0]
            changes["audio_settings"]["device"] = audioSettings.device;
        }
        content += `Audio Device: ${createDropdown(`audio_settings-device`, audioSettings.device_options, audioSettings.device)}<br>`;
    
    }
    for (let i = 1; i <= 3; i++) {
        if (audioSettings[`channel${i}`]) {
            content += `Channel ${i}: ${createInputField(`audio_settings-channel${i}`, "number", audioSettings[`channel${i}`])}`;
        }
        if (audioSettings[`sine${i}_freq`] && audioSettings[`sine${i}_volume`]) {
            content += `Test Sine Freq: ${createInputField(`audio_settings-sine${i}_freq`, "number", audioSettings[`sine${i}_freq`])}`;
            content += `Volume: ${createInputField(`audio_settings-sine${i}_volume`, "number", audioSettings[`sine${i}_volume`])}`;
            content += `${createButton(`test-sine${i}`, "Test")}${createButton(`stop-sine${i}`, "Stop")}<br>`;
        }
    }
    content += `${createButton("kill-all-test-sine", "Kill Test Sines")}<br>`;
    return content;
}

function createAudioModelSettingsContent(audioModelSettings) {
    let content = '';
    if (audioModelSettings.model_options) {
        content += `Model: ${createDropdown("audio_model_settings-model", audioModelSettings.model_options, audioModelSettings.model)}<br>`;
    }
    if (audioModelSettings.device_options) {
        content += `Device: ${createDropdown("audio_model_settings-device", audioModelSettings.device_options, audioModelSettings.device)}<br>`;
    }
    if (audioModelSettings.audio_length_in_s){
        content += `Audio Length: ${createInputField("audio_model_settings-negative_prompt-audio_length_in_s", "number", audioModelSettings.audio_length_in_s)}<br>`;
    }
    if (audioModelSettings.guidance_scale){
        //validation if whole int 
        content += `Guidance Scale: ${createInputField("audio_model_settings-negative_prompt-guidance_scale", "number", audioModelSettings.guidance_scale)}<br>`;
    }
    if (audioModelSettings.num_inference_steps){
        //validation if whole int 
        content += `Num Inference Steps: ${createInputField("audio_model_settings-negative_prompt-num_inference_steps", "number", audioModelSettings.num_inference_steps)}<br>`;
    }
    if (audioModelSettings.negative_prompt){
        content += `Negative Prompt: ${createInputField("audio_model_settings-negative_prompt", "text", audioModelSettings.negative_prompt)}<br>`;
    }
    return content;
}

function createLLMSettingsContent(llmSettings) {
    let content = '';
    if (llmSettings.number_soundevents){
        //validation if whole int 
        content += `Number Soundevents: ${createInputField("llm_settings-number_soundevents", "number", llmSettings.number_soundevents)}<br>`;
    }
    if (llmSettings. number_prompts){
        //validation if whole int 
        content += `Number Prompts: ${createInputField("llm_settings-number_prompts", "number", llmSettings.number_prompts)}<br>`;
    }
    if (llmSettings.role_system){
        content += `Role System: ${createInputField("llm_settings-role_system", "text", llmSettings.role_system, "long-input-text")}<br>`;
    }
    if (llmSettings.role_user){
        content += `Role User: ${createInputField("llm_settings-role_user", "text", llmSettings.role_user, "long-input-text")}<br>`;
    }
    return content;
}

function createDropdown(id, array, defaultValue) {
    return array.reduce((dropdown, item) => {
        const isSelected = item === defaultValue ? ' selected' : '';
        return `${dropdown}<option value="${item}"${isSelected}>${item}</option>`;
    }, `<select class="settings-dropdown" id="${id}">`) + "</select>";
}

function createInputField(id, type, value, html_class="settings-input") {
    return `<input class="${html_class}" type="${type}" id="${id}" value="${value}">`;
}

function createButton(id, text) {
    return `<button class="settings-button" id="${id}">${text}</button>`;
}

function createSettingsSection(settings, sectionName, contentGenerator) {
    return settings[sectionName] ? `<div class="${sectionName}"><h2>${sectionName.replace(/_/g, ' ')}</h2>${contentGenerator(settings[sectionName])}</div><br>` : '';
}

export { loadSettings, getSettingHTML, initializeSettingsListeners, saveSettings};