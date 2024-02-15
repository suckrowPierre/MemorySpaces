//TODO: implement caching of questions 

async function loadQuestionsAndAnswers() {
    try {
        const response = await fetch(endpoints.questions, {
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
            <p class="question">${question}</p>
            <input class="answer input-field" type="text" id="answer${index}">
        </div>
    `).join('') + `<div><button id="submit-answers" class="button">Submit Answers</button></div>`;
}

async function submitAnswers(id) {
    const answerElements = Array.from(document.getElementsByClassName("answer"));
    const answers = answerElements.map(el => el.value.trim());

    if (answers.some(answer => answer === "")) {
        alert("Please fill in all answers");
        return;
    }

    try {
        const response = await fetch(endpoints.generate, {
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


var parallelProcessorWS = null;

function connectGeneratWS() {
    console.log("Connecting to pp websocket");
    parallelProcessorWS = new WebSocket(`ws://${window.location.host}${endpoints.parallel_processor_ws}`);
    parallelProcessorWS.onopen = function() {
        console.log("Connected to pp websocket");
    };
    parallelProcessorWS.onerror = function(error) {
        console.error("WebSocket Error:", error);
    };
    parallelProcessorWS.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log("WebSocket message received:", data);
        if (data.memory_space_index == undefined) {
            updateBubbleSubtext(1, data.statusParallelProcessor);
            updateBubbleSubtext(2, data.statusParallelProcessor);
            updateBubbleSubtext(3, data.statusParallelProcessor);
        } 
        if (data.statusParallelProcessor && data.memory_space_index) {
            updateBubbleSubtext(data.memory_space_index, data.statusParallelProcessor);
        }

    };
    parallelProcessorWS.onclose = function(event) {
        console.log("Disconnected from pp websocket", event.reason);
    };
}


function updateBubbleSubtext(bubblenummer, subtext) {
    const bubble = document.getElementById(`bubble${bubblenummer}`);
    if (bubble) {
        bubble.getElementsByClassName("bubble-subtext")[0].textContent = subtext;
    }
}

export { loadQuestionsAndAnswers
, submitAnswers, connectGeneratWS};


