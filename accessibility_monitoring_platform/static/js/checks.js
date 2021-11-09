function setTextareaDisplay(checkboxElement, textareaElement) {
    if (checkboxElement.checked) {
        textareaElement.classList.remove("hidden-form");
    } else {
        textareaElement.classList.add("hidden-form");
    };
};

function addTogglesToFailedNotes(numberOfFailedNotes) {
    let index = 0;
    let checkboxElement = document.getElementById(`id_form-${index}-failed`);
    let textareaElement = document.getElementById(`id_form-${index}-notes`);
    while (checkboxElement !== null && textareaElement !== null) {
        setTextareaDisplay(checkboxElement, textareaElement);
        (function(checkboxElement, textareaElement) {
            checkboxElement.addEventListener("change", () => {
                setTextareaDisplay(checkboxElement, textareaElement);
            });
        })(checkboxElement, textareaElement);
        index++;
        checkboxElement = document.getElementById(`id_form-${index}-failed`);
        textareaElement = document.getElementById(`id_form-${index}-notes`);
    };
};

(function() {
    addTogglesToFailedNotes();
})();
