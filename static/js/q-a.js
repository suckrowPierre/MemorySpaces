async function loadQandA() {
    try {
        const response = await fetch('/questions', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const data = await response.json();
        if(data.questions){
            document.getElementById("modal-content").innerHTML = getQandABlock(data.questions);
            return Promise.resolve();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}


function getQandABlock(questions){
    var questionBlock = "";
    for (var i = 0; i < questions.length; i++){
        questionBlock += `
        <div class="question-answer">
        <h1 class="question">${questions[i]}</h1>
        <input class="answer" type="text" id="answer${i}"></input>
        </div>
        `
    }
    questionBlock += `<br><br><div><button id="submit-answers">Submit Answers</button></div>`
    return questionBlock;
}

async function submitAnswers(id) {
    const answerElements = document.getElementsByClassName("answer");
    const answers = [];

    for (let i = 0; i < answerElements.length; i++) {
        if (answerElements[i].value == "") {
            alert("Please fill in all answers");
            return; // Early return if any answer is empty
        }
        answers.push(answerElements[i].value);
    }

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id: id, answers: answers })
        });

        const data = await response.json();

        if (data.success) {
            return true;
        } else {
            alert("No successful response from server");
            return false; 
        }
    } catch (error) {
        console.error('Error:', error);
        alert("An error occurred while submitting your answers.");
    }
}


export { loadQandA, submitAnswers};


