# PDF Compressor (Local Web App)

A fast and local web application for compressing PDF files using Ghostscript, built with Flask, Tailwind CSS, and Dropzone.js. Process PDFs privately on your own machine.

## Setup & Run

### 1\. **Install Python & Ghostscript**

-   **Python 3.7+**: Ensure Python is installed on your system.
    
-   **Ghostscript**: [Download](https://www.ghostscript.com/download/gsdnld.html "null") and install Ghostscript. **Crucially, add its `bin` directory (e.g., `C:\Program Files\gs\gs10.05.1\bin`) to your system's `PATH` environment variable.**
    

### 2\. **Get the Code & Install Dependencies**

Open your terminal (Command Prompt/PowerShell) and run:

    git clone https://github.com/afifalhauzan/compress_pdf
    cd pdf-compressor
    pip install Flask
    

_(Note: This directly installs Flask. For larger projects or to ensure exact dependency versions, a `requirements.txt` file and a Python virtual environment are typically recommended.)_

### 3\. **Start the App**

    python app.py
    

Your browser should automatically open to `http://127.0.0.1:5000/`. If not, navigate there manually.

_Optional: For Windows users, double-click the `StartPDFCompressor.bat` file (if you created it) to automatically start the server and open the browser._

### 4\. **Use It!**

Drag & drop your PDF, select a compression quality, and click "Compress PDF". The compressed file will download automatically.

## 🐛 Troubleshooting

-   **`'gswin64c.exe' is not recognized`**: Ghostscript's `bin` directory is not in your system's `PATH`. See step 1.
    
-   **No download / Errors in console**: Check the terminal where `python app.py` is running for detailed error messages.

