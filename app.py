import os
from flask import Flask, request, send_file, render_template, after_this_request
from werkzeug.utils import secure_filename
import subprocess
import tempfile
import logging

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'flask_pdf_compressor_uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def compress_pdf(input_path, original_filename_for_output, quality='ebook'):
    logging.info(f"Starting compression for: {input_path} with quality: {quality}")

    # Determine output path for the compressed file
    # Ensure the output filename only gets 'compressed_' once
    output_filename = f'compressed_{quality}_{original_filename_for_output}'
    output_path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        output_filename
    )

    image_dpi_settings = {
        'screen': 72,
        'ebook': 150,
        'printer': 300,
        'prepress': 300,
        'default': 150
    }
    chosen_dpi = image_dpi_settings.get(quality, 150)

    command = [
        'gswin64c.exe',
        '-q',
        '-dBATCH',
        '-dNOPAUSE',
        '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.5',
        '-dColorConversionStrategy=/LeaveColorUnchanged',
        f'-dPDFSETTINGS=/{quality}',
        '-dEmbedAllFonts=true',
        '-dSubsetFonts=true',
        '-dAutoRotatePages=/None',
        '-dColorImageDownsampleType=/Bicubic',
        '-dGrayImageDownsampleType=/Bicubic',
        '-dMonoImageDownsampleType=/Subsample',
        f'-dGrayImageResolution={chosen_dpi}',
        f'-dColorImageResolution={chosen_dpi}',
        f'-dMonoImageResolution={chosen_dpi}',
        f'-sOutputFile={output_path}',
        input_path
    ]

    logging.info(f"Ghostscript command: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)

        logging.info(f"Ghostscript STDOUT:\n{result.stdout}")
        if result.stderr:
            logging.warning(f"Ghostscript STDERR:\n{result.stderr}")
        logging.info(f"Ghostscript exited with code: {result.returncode}")

        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Ghostscript failed to create output file at {output_path}")
        if os.path.getsize(output_path) == 0:
            raise ValueError(f"Ghostscript created an empty output file at {output_path}")

        logging.info(f"Compressed file created successfully at: {output_path} (Size: {os.path.getsize(output_path)} bytes)")
        return output_path

    except subprocess.CalledProcessError as e:
        error_msg = f"Ghostscript command failed with exit code {e.returncode}.\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}"
        logging.error(error_msg)
        raise Exception(f"PDF compression failed: {error_msg}") from e
    except FileNotFoundError as e:
        logging.error(f"File not found error after compression: {e}")
        raise
    except ValueError as e:
        logging.error(f"Value error after compression: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred during Ghostscript call: {e}")
        raise

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/compress', methods=['POST'])
def compress():
    logging.info("POST /compress request received.")
    
    if 'file' not in request.files:
        logging.warning("No 'file' part in request.files.")
        return jsonify(success=False, message='No file uploaded'), 400
    
    file = request.files['file']
    logging.info(f"Raw filename received from request.files: {file.filename}")

    if file.filename == '':
        logging.warning("No file selected (filename is empty).")
        return jsonify(success=False, message='No file selected'), 400
    
    if not file.filename.lower().endswith('.pdf'):
        logging.warning(f"Invalid file type uploaded: {file.filename}")
        return jsonify(success=False, message='Only PDF files are allowed'), 400
    
    original_filename = secure_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
    
    try:
        file.save(input_path)
        logging.info(f"Input file saved to: {input_path}")

        quality = request.form.get('quality', 'ebook')
        logging.info(f"Requested compression quality: {quality}")

        compressed_path = compress_pdf(input_path, original_filename, quality)
        
        # --- NEW: Return JSON response with download URL ---
        # Instead of sending the file directly from this route
        
        # Generate a unique ID or use the filename to create a temporary download URL
        # We'll create a new route /download/<filename> to serve it
        download_name = f'compressed_{quality}_{original_filename}'
        
        # Store compressed_path and original_filename in a temporary session or cache if needed
        # For simplicity, we'll just return the unique filename and let the new route handle path lookup
        
        # Clean up input file after processing is done
        @after_this_request
        def cleanup_input_only(response):
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
                    logging.info(f"Cleaned up input file: {input_path}")
            except Exception as e:
                logging.error(f"Error during input file cleanup: {e}")
            return response

        # Flask needs jsonify imported: from flask import jsonify, Flask, request, send_file, render_template, after_this_request
        from flask import jsonify 
        logging.info(f"Compression successful. Returning download URL for: {download_name}")
        return jsonify(success=True, download_filename=download_name, compressed_server_path=compressed_path)

    except Exception as e:
        logging.error(f"An error occurred during compression or file handling: {str(e)}")
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
                logging.info(f"Cleaned up input file after error: {input_path}")
        except Exception as cleanup_e:
            logging.error(f"Error cleaning up input file after compression error: {cleanup_e}")
        return jsonify(success=False, message=f'Error compressing PDF: {str(e)}'), 500

# --- NEW ROUTE TO SERVE THE COMPRESSED FILE ---
@app.route('/download/<filename>', methods=['GET'])
def download_compressed_pdf(filename):
    # Reconstruct the path to the compressed file in the temp folder
    compressed_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    logging.info(f"Download request received for: {filename} at path: {compressed_file_path}")

    if not os.path.exists(compressed_file_path):
        logging.warning(f"Download request for non-existent file: {compressed_file_path}")
        return "File not found.", 404
    
    @after_this_request
    def cleanup_output_after_download(response):
        try:
            if os.path.exists(compressed_file_path):
                os.remove(compressed_file_path)
        except Exception as e:
            logging.error(f"Error during output file cleanup after download: {e}")
        return response

    return send_file(
        compressed_file_path,
        as_attachment=True,
        download_name=filename, # Use the filename passed in the URL as download_name
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)