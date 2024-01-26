const loginContent = `
    <h1>Login</h1>
    <input type="password" id="passwordInput">
`;

function hashPassword(password) {
    return CryptoJS.MD5(password).toString();
}

async function submitPassword(password) {
    const hashedPassword = hashPassword(password); 
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password: hashedPassword }),
        });

        const data = await response.json();

        if (data.success) {
            return true; 
        } else {
            return false;
        }
    } catch (error) {
        console.error('Error:', error);
        return false;
    }
}


export { loginContent, submitPassword };