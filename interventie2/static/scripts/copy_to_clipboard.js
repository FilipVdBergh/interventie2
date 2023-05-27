function copy_to_clipboard(element_id) {
    // Get the text field
    var copyText = document.getElementById(element_id);
  
    // Select the text field
    copyText.select();
    copyText.setSelectionRange(0, 99999); // For mobile devices
  
     // Copy the text inside the text field
    navigator.clipboard.writeText(copyText.value);
  
    // Alert the copied text
    alert("De tekst is gekopiëerd. \n[" + copyText.value + "]");
  }