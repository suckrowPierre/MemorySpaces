import { loginContent, submitPassword } from './login.js';
import { loadQuestionsAndAnswers, submitAnswers } from './q-a.js';
import { getSettingHTML, loadSettings } from './settings.js';

var modal = document.getElementById("modal");

document.addEventListener("click", (event) => {
    const { id } = event.target;
    if (id === "settings") openSettings();
    else if (id === "close-modal") closeModal();
    else if (id.startsWith("bubble")) bubbleClicked(parseInt(id[id.length - 1]));
});

async function openSettings() {
    openModal(loginContent);
    const passwordInput = document.getElementById('passwordInput');
    passwordInput.addEventListener('keydown', async (event) => {
        if (event.key === 'Enter') {
            const password = passwordInput.value;
            const isSuccess = await submitPassword(password);
            if (isSuccess) {
                document.getElementById("modal-content").textContent = "Logged in successfully. Loading data...";
                const settings = await loadSettings();
                console.log(settings);
                if (settings) {
                    document.getElementById("modal-content").innerHTML = getSettingHTML(settings);
                }
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
