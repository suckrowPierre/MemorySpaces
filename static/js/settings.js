function getDropdownFromArray(array, id){
    var dropdown = `<select class="dorpdown" id="${id}">`;
    for (option of array){
        dropdown += `<option value="${option}">${option}</option>`;
    }
    dropdown += "</select>";
}

async function loadSettings()
{
    const response = await fetch('/settings', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    const data = await response.json();
    if (data.settings) {
        return data.settings;
    }
}

export { loadSettings };