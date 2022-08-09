const feedbackForm = document.getElementById('feedback-form')
const feedbackBanner = document.getElementById('feedback-banner')
const showFeedbackFormButtom = document.getElementById('show_feedback_form')
const hideFeedbackFormButtom = document.getElementById('hide_feedback_form')
const hiddenForm = ' hide-form'

showFeedbackFormButtom.onclick = function () {
  if (feedbackForm.className.includes(hiddenForm)) {
    feedbackForm.className = feedbackForm.className.replace(hiddenForm, '')
  } else {
    feedbackForm.className += hiddenForm
  }

  if (feedbackBanner.className.includes(hiddenForm)) {
    feedbackBanner.className = feedbackBanner.className.replace(hiddenForm, '')
  } else {
    feedbackBanner.className += hiddenForm
  }
}

hideFeedbackFormButtom.onclick = function () {
  if (feedbackForm.className.includes(hiddenForm)) {
    feedbackForm.className = feedbackForm.className.replace(hiddenForm, '')
  } else {
    feedbackForm.className += hiddenForm
  }

  if (feedbackBanner.className.includes(hiddenForm)) {
    feedbackBanner.className = feedbackBanner.className.replace(hiddenForm, '')
  } else {
    feedbackBanner.className += hiddenForm
  }
}
