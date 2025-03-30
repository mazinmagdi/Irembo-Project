Prerequisites

Python 3.8 or higher
pip (Python package manager)
Virtual environment (recommended)
Installation

Clone the repository:

git clone https://github.com/adamlogman/Irembo-Project.git
cd Irembo-Project
Create and activate a virtual environment:

# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
Install the required dependencies:

pip install -r requirements.txt
Running the Application

Start the Flask development server:

python app.py
Open your web browser and navigate to:

http://127.0.0.1:5000/
Project Structure

Irembo-Project/
├── app.py
├── templates/
│       ├── index.html
├── requirements.txt
└── README.md
Development

To add new features or fix bugs:

Create a new branch:

git checkout -b feature/your-feature-name
Make your changes and commit them:

git add .
git commit -m "Add your feature description"
Push your changes to the repository:

git push origin feature/your-feature-name
Testing

Run the test suite with:

pytest
Deployment

For production deployment:

Set up a production server (e.g., Gunicorn, uWSGI)
Configure a reverse proxy (e.g., Nginx, Apache)
Set appropriate environment variables for production
Example with Gunicorn:

pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
License

This project is licensed under the MIT License - see the LICENSE file for details.
