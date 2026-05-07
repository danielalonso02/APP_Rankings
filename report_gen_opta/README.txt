📚 Required Libraries

Make sure to install the following libraries (in addition to standard ones like pandas, numpy, etc.):

pip install mplsoccer
pip install highlight_text
pip install openai==0.28.0
pip install reportlab

📁 Project Structure

Place all .py files and the following Excel files in the same root folder:
	•	Glossary.xlsx
	•	2RFEF_wyscout.xlsx
	•	parameters.xlsx
	•	.env file - contains your OpenAI API key
		Note: The .env file must include the following line:
			OPENAI_API_KEY=your_api_key_here
			

Inside that root folder, ensure you have the following two subfolders:

🔹 Logos:
	•	Contains all images used in the generated reports.

🔹 datoswyscout:
	•	Contains weight data for each playing position’s parameters.

To ensure the code runs correctly, you must execute it from within the main project folder (i.e., the same directory where all .py files and required resources are located).
