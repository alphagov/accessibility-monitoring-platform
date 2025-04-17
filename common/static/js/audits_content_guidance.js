/*
Add content guidance to each WCAG criteria, and shows when criteria has been met
*/

window.undoData = {}

function convertMarkdownToNumberedList(markdown) {
  const lines = markdown.split('\n');
  let count = 1;

  return lines.map(line => {
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      // Replace bullet with numbered item
      return `${count++}. ${line.trim().slice(1).trim()}`;
    } else {
      return line; // Leave other lines untouched
    }
  }).join('\n');
}

function detectBulletPointsAndReturnGuidance(content, targetId) {
  const newlLineCount = (content.match(/\n/g) || []).length
  const bulletPointCount = (content.match(/^\s*[-*+]\s.+$/gm) || []).length
  const linkId = `bullet-point-conversion-${targetId}`
  const undoId = `bullet-point-conversion-undo-${targetId}`
  let adviceText = ''
  if ((newlLineCount && bulletPointCount > 1) || window.undoData[targetId]) {
    if (!window.undoData[targetId]) {
      const elementButton = document.getElementById(`content-guidance-${targetId}`)
      if (!elementButton.dataset.listenerAdded) {
        elementButton.addEventListener('click', function(event) {
            const textElement = document.getElementById(targetId)
  
            if (event.target && event.target.id === (linkId)) {
              event.preventDefault();

              window.undoData[targetId] = textElement.value
              textElement.value = convertMarkdownToNumberedList(textElement.value)
  
              textElement.dispatchEvent(new Event('input', { bubbles: true }))
            }  else if (event.target && event.target.id === (undoId) && window.undoData[targetId]) {
              event.preventDefault();

              const textElement = document.getElementById(targetId)
              textElement.value = window.undoData[targetId]
              window.undoData[targetId] = undefined
  
              textElement.dispatchEvent(new Event('input', { bubbles: true }))
            }
          },
        );
        elementButton.dataset.listenerAdded = true
      }
    }
    if (!window.undoData[targetId]) {
      adviceText += `Numbered lists improve clarity when raising specific issues with the organisation. Try <a href="#" id="${linkId}" class="govuk-link govuk-link--no-visited-state">converting the bullet points into a numbered list</a>. `
    } else {
      adviceText +=  `Numbered lists improve clarity when raising specific issues with the organisation. Try converting the bullet points into a numbered list. <a href="#" id="${undoId}" class="govuk-link govuk-link--no-visited-state">Undo</a>.`
    }
    return adviceText
  }
  return ''
}

function contentGuidanceCalculation(targetId, content) {
  let targetElement = document.getElementById(`amp-content-guidance-container-${targetId}`)
  let targetElementContent = document.getElementById(`content-guidance-${targetId}`)
  const guidance = detectBulletPointsAndReturnGuidance(content, targetId)
  if (guidance || window.undoData[targetId]) {
    targetElement.style.display = 'block'
  } else {
    targetElement.style.display = 'none'
  }
  targetElementContent.innerHTML = guidance
}

const contentGuidanceElements = document.getElementsByClassName('amp-content-guidance')

Array.from(contentGuidanceElements).forEach(function (contentGuidanceElement) {
  const contentGuidanceElementId = contentGuidanceElement.id
  const inputId = contentGuidanceElementId.replace('content-guidance-', '')
  const inputElement = document.getElementById(inputId)
  inputElement.addEventListener('input', function(e) {
      contentGuidanceCalculation(inputId, e.target.value)
    }
  )
})
