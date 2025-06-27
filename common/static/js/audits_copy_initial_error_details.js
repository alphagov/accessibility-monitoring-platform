const contentGuidanceElements = document.getElementsByClassName('amp-initial-report-text')

Array.from(contentGuidanceElements).forEach(function (contentGuidanceElement) {
  const int_element = contentGuidanceElement.id.replace('amp-report-content-copy-', '')
  contentGuidanceElement.addEventListener('click', function(e) {
    e.preventDefault();
    const inputArea = document.getElementById(`id_form-${int_element}-retest_notes`)
    inputArea.value = contentGuidanceElement.dataset.reportText
    inputArea.dispatchEvent(new Event('input', { bubbles: true }))
  });
});
