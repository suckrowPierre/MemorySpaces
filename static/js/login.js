const loginContent = `
    <h1>Login</h1>
    <input type="password" id="passwordInput">
`;

function hashPassword(password) {
    return CryptoJS.MD5(password).toString();
}

async function submitPassword(password) {
    const hashedPassword = await hashPassword(password); 
    try {
        const response = await fetch(endpoints.login, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password: hashedPassword }),
        });

        const data = await response.json();
        return data.success;
    } catch (error) {
        console.error('Error:', error);
        return false;
    }
}


export { loginContent, submitPassword };