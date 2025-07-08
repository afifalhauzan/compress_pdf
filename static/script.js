Dropzone.autoDiscover = false;

const compressButton = document.getElementById('compressButton');
const buttonLoader = document.getElementById('buttonLoader');
const buttonText = document.getElementById('buttonText');

// Initialize Dropzone
let myDropzone = new Dropzone("#my-dropzone-form", {
  url: "/compress",
  paramName: "file",
  maxFiles: 1,
  acceptedFiles: ".pdf",
  autoProcessQueue: false,
  addRemoveLinks: true,
  dictDefaultMessage: "Drag & Drop PDF here or click to select",
  dictFallbackMessage: "Your browser does not support drag'n'drop file uploads.",
  dictRemoveFile: "Remove file",
  dictFileTooBig: "File is too big ({{filesize}}MB). Max filesize: {{maxFilesize}}MB.",
  dictInvalidFileType: "You can't upload files of this type.",

  forceChunking: false, // Ensures it's treated as a single file upload
  uploadMultiple: false, // Ensure single file upload behavior
  createImageThumbnails: false, // Often not needed for PDFs, saves resources
});


myDropzone.on("addedfile", file => {
  console.log(`File added: ${file.name}`);
  // Optional: You might want to automatically process the queue here
  // if you want immediate upload on drop/selection.
  // myDropzone.processQueue();
});

document.querySelector("button[type=submit]").addEventListener("click", function (e) {
  e.preventDefault();
  e.stopPropagation();

  if (myDropzone.getQueuedFiles().length > 0) {
    myDropzone.processQueue();
  } else {
    Toastify({
      text: "Please select a PDF file first!",
      duration: 3000,
      close: true,
      gravity: "top",
      position: "center",
      style: {
        background: "linear-gradient(to right, #ff416c, #ff4b2b)",
      },
    }).showToast();
  }
});

myDropzone.on("processing", function () {
  buttonLoader.classList.add('active'); // Show loader
  buttonText.style.opacity = '0';      // Hide text
  buttonText.style.pointerEvents = 'none'; // Make text unclickable when hidden
  compressButton.disabled = true;      // Disable button
});

myDropzone.on("queuecomplete", function () {
  if (myDropzone.getUploadingFiles().length === 0 && myDropzone.getQueuedFiles().length === 0) {
    buttonLoader.classList.remove('active'); // Hide loader
    buttonText.style.opacity = '1';       // Show text
    buttonText.style.pointerEvents = 'auto'; // Make text clickable again
    compressButton.disabled = false;       // Re-enable button
  }
});

myDropzone.on("success", function (file, response) {
  console.log("File uploaded and processed successfully!", response);
  // 'response' here will be the JSON from your Flask server

  // Check if the server indicated success and provided a download filename
  if (response && response.success && response.download_filename) {
    const downloadUrl = `/download/${response.download_filename}`;
    console.log("Download URL generated:", downloadUrl);
    // Trigger the download by navigating the browser to the new URL
    window.location.href = downloadUrl; // This will trigger a new GET request to /download/<filename>

    Toastify({
      text: "Download Success! Check your browser's download folder.",
      duration: 3000,
      newWindow: true,
      close: true,
      gravity: "top", // `top` or `bottom`
      position: "center", // `left`, `center` or `right`
      stopOnFocus: true, // Prevents dismissing of toast on hover
      style: {
        background: "linear-gradient(to right, #00b09b, #96c93d)",
      },
      onClick: function () { } // Callback after click
    }).showToast();

    myDropzone.removeFile(file); // Remove from Dropzone's visual preview
  } else {
    console.error("Server did not return a successful download filename:", response);
    alert("Error: Server did not return a valid download link.");
    myDropzone.removeFile(file); // Remove on error
  }
});

myDropzone.on("error", function (file, message, xhr) { // xhr contains server response if any
  console.error("Error during upload or compression:", message);
  // Try to parse server's error message if available
  let errorMessage = message;
  if (xhr && xhr.response) {
    try {
      const serverResponse = JSON.parse(xhr.response);
      errorMessage = serverResponse.message || message;
    } catch (e) {
      // response was not JSON, use original message
    }
  }
  alert(`Error processing file: ${errorMessage}`);
  myDropzone.removeFile(file);
});

myDropzone.on("sending", function (file, xhr, formData) {
  // Append the selected quality to the form data
  const selectedQuality = document.querySelector('input[name="quality"]:checked').value;
  formData.append("quality", selectedQuality);
  console.log("Sending with quality:", selectedQuality);
});