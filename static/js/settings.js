async function loadSettings() {
    const response = await fetch('/settings', { method: 'GET', headers: { 'Content-Type': 'application/json' } });
    const data = await response.json();
    return data.settings || {};
}

function getSettingHTML(settings) {
    return `<div class="settings">
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
        content += `Audio Device: ${createDropdown(audioSettings.device_options, audioSettings.device, "devices-dropdown")}<br>`;
    }
    for (let i = 1; i <= 3; i++) {
        if (audioSettings[`channel${i}`]) {
            content += `Channel ${i}: ${createInputField(`channel${i}`, "number", audioSettings[`channel${i}`])}`;
        }
        if (audioSettings[`sine${i}_freq`] && audioSettings[`sine${i}_volume`]) {
            content += `Test Sine Freq: ${createInputField(`sine${i}_freq`, "number", audioSettings[`sine${i}_freq`])}`;
            content += `Volume: ${createInputField(`sine${i}_volume`, "number", audioSettings[`sine${i}_volume`])}`;
            content += `${createButton(`test-sine${i}`, "Test")}${createButton(`stop-sine${i}`, "Stop")}<br>`;
        }
    }
    content += `${createButton("kill-all-test-sine", "Kill Test Sines")}<br>`;
    return content;
}

function createAudioModelSettingsContent(audioModelSettings) {
    let content = '';
    if (audioModelSettings.model_options) {
        content += `Model: ${createDropdown(audioModelSettings.model_options, audioModelSettings.model, "model-dropdown")}<br>`;
    }
    if (audioModelSettings.device_options) {
        content += `Device: ${createDropdown(audioModelSettings.device_options, audioModelSettings.device, "device-dropdown")}<br>`;
    }
    if (audioModelSettings.audio_length_in_s){
        content += `Audio Length: ${createInputField("audio-length", "number", audioModelSettings.audio_length_in_s)}<br>`;
    }
    if (audioModelSettings.guidance_scale){
        //validation if whole int 
        content += `Guidance Scale: ${createInputField("guidance-scale", "number", audioModelSettings.guidance_scale)}<br>`;
    }
    if (audioModelSettings.num_inference_steps){
        //validation if whole int 
        content += `Num Inference Steps: ${createInputField("num-inference-steps", "number", audioModelSettings.num_inference_steps)}<br>`;
    }
    if (audioModelSettings.negative_prompt){
        content += `Negative Prompt: ${createInputField("negative-prompt", "text", audioModelSettings.negative_prompt, "long-input-text")}<br>`;
    }
    return content;
}

function createLLMSettingsContent(llmSettings) {
    let content = '';
    if (llmSettings.number_soundevents){
        //validation if whole int 
        content += `Number Soundevents: ${createInputField("number-soundevents", "number", llmSettings.number_soundevents)}<br>`;
    }
    if (llmSettings. number_prompts){
        //validation if whole int 
        content += `Number Prompts: ${createInputField("number-prompts", "number", llmSettings.number_prompts)}<br>`;
    }
    if (llmSettings.role_system){
        content += `Role System: ${createInputField("role-system", "text", llmSettings.role_system, "long-input-text")}<br>`;
    }
    if (llmSettings.role_user){
        content += `Role User: ${createInputField("role-user", "text", llmSettings.role_user, "long-input-text")}<br>`;
    }
    return content;
}

function createDropdown(array, defaultValue, id ) {
    return array.reduce((dropdown, item) => {
        const isSelected = item === defaultValue ? ' selected' : '';
        return `${dropdown}<option value="${item}"${isSelected}>${item}</option>`;
    }, `<select class="dropdown" id="${id}">`) + "</select>";
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

export { loadSettings, getSettingHTML};