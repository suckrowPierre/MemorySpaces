const loginContent = `
    <h1>Login</h1>
    <input type="password" id="passwordInput">
`;

function hashPassword(password) {
    return CryptoJS.MD5(password).toString();
}

function submitPassword() {
    var password = document.getElementById("passwordInput").value;
    var hashedPassword = hashPassword(password);

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password: hashedPassword }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById("modal-content").innerHTML = "Logged in successfully. Loading data...";
        }
    });
}

export { loginContent, submitPassword };