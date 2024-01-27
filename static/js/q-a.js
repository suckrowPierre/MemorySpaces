//TODO: implement caching of questions 

async function loadQuestionsAndAnswers() {
    try {
        const response = await fetch('/questions', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const data = await response.json();
        if (data.questions) {
            document.getElementById("modal-content").innerHTML = getQuestionsAndAnswersBlock(data.questions);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function getQuestionsAndAnswersBlock(questions) {
    return questions.map((question, index) => `
        <div class="question-answer">
            <h1 class="question">${question}</h1>
            <input class="answer" type="text" id="answer${index}">
        </div>
    `).join('') + `<br><br><div><button id="submit-answers">Submit Answers</button></div>`;
}

async function submitAnswers(id) {
    const answerElements = Array.from(document.getElementsByClassName("answer"));
    const answers = answerElements.map(el => el.value.trim());

    if (answers.some(answer => answer === "")) {
        alert("Please fill in all answers");
        return;
    }

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id, answers })
        });

        const data = await response.json();
        if (!data.success) {
            alert("No successful response from server");
        }
        return data.success;
    } catch (error) {
        console.error('Error:', error);
        alert("An error occurred while submitting your answers.");
        return false;
    }
}


export { loadQuestionsAndAnswers
, submitAnswers};


