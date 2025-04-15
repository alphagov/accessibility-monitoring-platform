/*
Add content guidance to each WCAG criteria, and shows when criteria has been met
*/

function myHandlerFunction() {
  console.log('Ha it worked')
}

function detectBulletPointsAndReturnGuidance(content, targetId) {
  const newlLineCount = (content.match(/\n/g) || []).length
  const bulletPointCount = (content.match(/^\s*[-*+]\s.+$/gm) || []).length
  if (newlLineCount && bulletPointCount > 1) {
    const linkId = `bullet-point-converion-${targetId}`
    return `Numbered lists make it easier to communicate individual issues with the organisation. Try <a href="#" id="${linkId}">converting the bullet points into a numbered list.</a>`
  }
  return ''
}

function contentGuidanceCalculation(targetId, content) {
  let targetElement = document.getElementById(`amp-content-guidance-container-${targetId}`)
  let targetElementContent = document.getElementById(`content-guidance-${targetId}`)
  const guidance = detectBulletPointsAndReturnGuidance(content, targetId)
  if (guidance) {
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
  inputElement.addEventListener(
    'input',
    function(e) {
      contentGuidanceCalculation(inputId, e.target.value)
    }
  )
})

console.log("imported JS")
