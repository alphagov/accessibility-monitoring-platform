/*
Allow user to open link entered in URL field using dynamic link
*/

function updateOpenLinkControl(openLinkControlId, value) {
    const openLinkControlElement = document.getElementById(openLinkControlId)
    if (value.includes("https://") == false) {
        openLinkControlElement.classList.add("amp-open-link-control-disabled")
        openLinkControlElement.classList.remove("amp-open-link-control-enabled")
        openLinkControlElement.setAttribute("href", "javascript:;")
        openLinkControlElement.setAttribute("target", "")
    } else {
        openLinkControlElement.classList.add("amp-open-link-control-enabled")
        openLinkControlElement.classList.remove("amp-open-link-control-disabled")
        openLinkControlElement.setAttribute("href", value)
        openLinkControlElement.setAttribute("target", "_blank")
    }
}


const openLinkControlElements = document.getElementsByClassName("amp-open-link-control")

Array.from(openLinkControlElements).forEach(function(openLinkControlElement) {
    const openLinkControlId = openLinkControlElement.getAttribute("id")
    const linkFieldId = openLinkControlElement.getAttribute("fieldId")
    const linkFieldElement = document.getElementById(linkFieldId)
    updateOpenLinkControl(openLinkControlId, linkFieldElement.value)
    linkFieldElement.addEventListener(
        "input", (event) => updateOpenLinkControl(openLinkControlId, event.target.value)
    )
})

// module.exports = {
//     updateOpenLinkControl,
// }
