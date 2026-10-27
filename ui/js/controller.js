$(document).ready(function () {
  // display speak message
  function DisplayMessage(message) {
    const $msg = $(".siri-message");
    if ($msg.find("li").length) $msg.find("li:first").text(message);
    else $msg.text(message);
    if ($msg.textillate) $msg.textillate("start");
  }
  eel.expose(DisplayMessage);

  function animateOvalContainer() {
    const oval = document.getElementById("Oval");
    if (!oval) return;
    const container = oval.closest(".container") || oval; // animate the whole container
    container.classList.remove("zoom-in-soft"); // restart if already applied
    void container.offsetWidth; // reflow
    container.classList.add("zoom-in-soft");
  }

  // display hood
  eel.expose(ShowHood);
  function ShowHood() {
    $("#Oval").attr("hidden", false);
    $("#SiriWave").attr("hidden", true);
    // animateOvalContainer();
  }

  // show the listening wave (used when "Hey Ivy" is heard)
  eel.expose(ShowSiriWave);
  function ShowSiriWave() {
    $("#Oval").attr("hidden", true);
    $("#SiriWave").attr("hidden", false);
  }

  // chat text comes from speech and the news API, so never treat it as HTML
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // insertAdjacentHTML appends without re-parsing the whole chat history
  function appendChat(className, justify, message) {
    var chatBox = document.getElementById("chat-canvas-body");
    if (message.trim() !== "") {
      chatBox.insertAdjacentHTML(
        "beforeend",
        `<div class="row ${justify} mb-4">
            <div class = "width-size">
            <div class="${className}">${escapeHtml(message)}</div>
            </div>
        </div>`
      );

      chatBox.scrollTop = chatBox.scrollHeight;
    }
  }

  eel.expose(senderText);
  function senderText(message) {
    appendChat("sender_message", "justify-content-end", message);
  }

  eel.expose(receiverText);
  function receiverText(message) {
    appendChat("receiver_message", "justify-content-start", message);
  }

  // Hide Loader and display Face Auth animation
  eel.expose(hideLoader);
  function hideLoader() {
    $("#Loader").attr("hidden", true);
    $("#FaceAuth").attr("hidden", false);
  }
  // Hide Face auth and display Face Auth success animation
  eel.expose(hideFaceAuth);
  function hideFaceAuth() {
    $("#FaceAuth").attr("hidden", true);
    $("#FaceAuthSuccess").attr("hidden", false);
  }
  // Hide success and display
  eel.expose(hideFaceAuthSuccess);
  function hideFaceAuthSuccess() {
    $("#FaceAuthSuccess").attr("hidden", true);
    $("#HelloGreet").attr("hidden", false);
  }

  // Hide Start Page and display blob
  eel.expose(hideStart);
  function hideStart() {
    $("#Start").attr("hidden", true);

    setTimeout(function () {
      $("#Oval").addClass("animate__animated animate__zoomIn");
    }, 1000);
    setTimeout(function () {
      $("#Oval").attr("hidden", false);
    }, 1000);
  }
});
