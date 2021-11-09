function setTextareaDisplay(checkboxElement, textareaElement) {
    if (checkboxElement.checked) {
        textareaElement.classList.remove("hidden-form");
    } else {
        textareaElement.classList.add("hidden-form");
    };
};

export function addTogglesToFailedNotes(numberOfFailedNotes) {
    [...Array(numberOfFailedNotes).keys()].forEach(index => {
        const checkboxElement = document.getElementById(`id_form-${index}-failed`);
        const textareaElement = document.getElementById(`id_form-${index}-notes`);
        setTextareaDisplay(checkboxElement, textareaElement)
        checkboxElement.addEventListener("change", () => setTextareaDisplay(checkboxElement, textareaElement));
    });
};
