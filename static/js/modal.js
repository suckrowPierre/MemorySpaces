import { loginContent, submitPassword } from './login.js';
import { loadQuestionsAndAnswers, submitAnswers, connectGeneratWS } from './q-a.js';
import { getSettingHTML, loadSettings, initializeSettingsListeners, saveSettings, startProgramm } from './settings.js';

var modal = document.getElementById("modal");

connectGeneratWS();

document.addEventListener("click", (event) => {
    const { id } = event.target;
    if (id === "settings") openSettings();
    else if (id === "close-modal") closeModal();
    else if (id.startsWith("bubble")) bubbleClicked(parseInt(id[id.length - 1]));
    else if (id === "load-settings-from-disk") loadAndUpdateSettings(true);
    else if (id === "save-settings") saveSettings();
    else if (id === "start-programm") {
        startProgramm();
        closeModal();
        //TODO
    }
});



async function loadAndUpdateSettings(fromDisk=false) {
    const settings = await loadSettings(fromDisk);
    if (settings) {
        console.log("settings", settings);
        document.getElementById("modal-content").innerHTML = getSettingHTML(settings);
        initializeSettingsListeners();
    }
}

async function openSettings() {
    openModal(loginContent);
    const passwordInput = document.getElementById('passwordInput');
    passwordInput.addEventListener('keydown', async (event) => {
        if (event.key === 'Enter') {
            const password = passwordInput.value;
            const isSuccess = await submitPassword(password);
            if (isSuccess) {
                document.getElementById("modal-content").textContent = "Logged in successfully. Loading data...";
                loadAndUpdateSettings();
            }
        }
    });
}

async function bubbleClicked(index) {
    openModal("loading...");
    try {
        await loadQuestionsAndAnswers();
        const submitButton = document.getElementById("submit-answers");
        if (submitButton) {
            submitButton.onclick = async () => {
                const isSuccess = await submitAnswers(index);
                if (isSuccess) closeModal();
            };
        } 
    } catch (error) {
        console.error('Error in loadQuestionsAndAnswers:', error);
    }
}

function openModal(content) {
    modal.style.display = "block";
    document.getElementById("modal-content").innerHTML = content;
}

function closeModal() {
    modal.style.display = "none";
}

export { openModal, closeModal };
