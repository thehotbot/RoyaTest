# The Hot Bot Demo

This is a Flask-based web application that simulates an SMS environment and includes a revenue calculator. It uses OpenAI's API for chat completions and features a customizable interface.

## Features

- SMS Simulator with OpenAI integration
- Revenue Calculator
- Customizable settings (API key, app title, logo)
- Session-based authentication

## Requirements

- Python 3.11
- Flask
- OpenAI API
- Tailwind CSS

## Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set up your environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `LOGIN_PASSWORD`: Password for accessing the application

## Running the Application

To run the application, use the following command:

```
python main.py
```

The application will be available at `http://localhost:5000`.

## Deployment on Replit

This application is configured to run on Replit. The necessary configuration is already set up in the `.replit` file.

To deploy:
1. Fork this repository to your Replit account.
2. Set up the required secrets in the Replit environment.
3. Click the "Run" button in Replit.

## Configuration

You can customize the application settings through the web interface after logging in.

## License

This project is open-source and available under the MIT License.
