/*
Applies ellipsis to the centre of the filename in case files manager
*/

function applyMiddleEllipsis(element, maxLength = 30) {
    if (!element) return;

    const text = element.innerText.trim();

    if (text.length <= maxLength) return;

    const ellipsis = '…';
    const charsToShow = maxLength - ellipsis.length;

    const frontChars = Math.ceil(charsToShow / 2);
    const backChars = Math.floor(charsToShow / 2);

    const truncated =
        text.substring(0, frontChars) +
        ellipsis +
        text.substring(text.length - backChars);

    element.innerText = truncated;
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".apply_ellipsis a").forEach(link => {
        link.title = link.innerText;
        applyMiddleEllipsis(link, 80);
    });
});