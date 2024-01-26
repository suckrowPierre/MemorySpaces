import { loginContent, submitPassword } from './login.js';

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
    openModal('Bubble ' + index + ' clicked');
}

function openModal(content) {
    modal.style.display = "block";
    // append content to modal
    document.getElementById("modal-content").innerHTML = content; // Use the 'content' variable
}

function closeModal() {
    modal.style.display = "none";
}


