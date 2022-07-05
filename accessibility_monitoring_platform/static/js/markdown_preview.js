const showdown  = require('showdown')
const converter = new showdown.Converter()

function previewMarkdown(sourceId, targetId) {
    const markdown = document.getElementById(sourceId).value
    const targetElement = document.getElementById(targetId)
    targetElement.innerHTML = converter.makeHtml(markdown)
}


const previewElements = document.getElementsByClassName('amp-preview')

Array.from(previewElements).forEach(function(previewElement) {
    const previewId = previewElement.id
    const inputId = previewId.replace('preview-', '')
    const inputElement = document.getElementById(inputId)
    inputElement.oninput = function() {
        previewMarkdown(inputId, previewId)
    }
    previewMarkdown(inputId, previewId)
})
