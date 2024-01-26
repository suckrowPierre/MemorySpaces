import { loginContent, submitPassword } from './login.js';
import { loadQandA, submitAnswers } from './q-a.js';

var modal = document.getElementById("modal");

document.getElementById("settings").addEventListener("click", openSettings);
document.getElementById("close-modal").addEventListener("click", closeModal);
document.getElementById("bubble1").addEventListener("click", () => bubbleClicked(1));
document.getElementById("bubble2").addEventListener("click", () => bubbleClicked(2));
document.getElementById("bubble3").addEventListener("click", () => bubbleClicked(3));

function openSettings() {
    openModal(loginContent);
    document.getElementById('passwordInput').addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            submitPassword();
        }
    });
}

function bubbleClicked(index) {
    openModal("loading...");
    loadQandA().then(() => {
        let submitButton = document.getElementById("submit-answers");
        if (submitButton) {
            submitButton.addEventListener("click", async () => {
                const success = await submitAnswers(index);
                if (success) {
                    closeModal();
                }
            });
        }
    }).catch(error => {
        console.error('Error in loadQandA:', error);
    });
}

function openModal(content) {
    modal.style.display = "block";
    document.getElementById("modal-content").innerHTML = content;
}

function closeModal() {
    modal.style.display = "none";
}

export { openModal, closeModal };
