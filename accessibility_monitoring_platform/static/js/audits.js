function setTextareaDisplay(checkboxElement, textareaElement, textareaLabelElement) {
  if (checkboxElement.checked) {
    textareaElement.classList.remove('hidden-form')
    textareaLabelElement.classList.remove('hidden-form')
  } else {
    textareaElement.classList.add('hidden-form')
    textareaLabelElement.classList.add('hidden-form')
  };
};

function addTogglesToFailedNotes(prefix) {
  let index = 0
  let checkboxElement = document.getElementById(`id_${prefix}-${index}-failed`)
  let textareaElement = document.getElementById(`id_${prefix}-${index}-notes`)
  let textareaLabelElement = document.getElementById(`id_${prefix}-${index}-notes-label`)
  while (checkboxElement !== null && textareaElement !== null && textareaLabelElement !== null) {
    setTextareaDisplay(checkboxElement, textareaElement, textareaLabelElement);
    (function (checkboxElement, textareaElement, textareaLabelElement) {
      checkboxElement.addEventListener('change', () => {
        setTextareaDisplay(checkboxElement, textareaElement, textareaLabelElement)
      })
    })(checkboxElement, textareaElement, textareaLabelElement)
    index++
    checkboxElement = document.getElementById(`id_${prefix}-${index}-failed`)
    textareaElement = document.getElementById(`id_${prefix}-${index}-notes`)
    textareaLabelElement = document.getElementById(`id_${prefix}-${index}-notes-label`)
  };
};

(function () {
  addTogglesToFailedNotes('form')
  addTogglesToFailedNotes('manual')
})()
