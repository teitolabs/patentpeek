# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from google_generate_query import generate_google_patents_query 

app = Flask(__name__)
CORS(app)

@app.route('/api/generate-google-query', methods=['POST'])
def handle_generate_google_query():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    structured_search_conditions = data.get('structured_search_conditions')
    inventors = data.get('inventors')
    assignees = data.get('assignees')
    after_date = data.get('after_date')
    after_date_type = data.get('after_date_type')
    before_date = data.get('before_date')
    before_date_type = data.get('before_date_type')
    patent_offices_list = data.get('patent_offices')
    
    languages_list = data.get('languages') # CHANGED: Expecting a list for languages

    status = data.get('status')
    patent_type = data.get('patent_type')
    litigation = data.get('litigation')
    dedicated_cpc = data.get('dedicated_cpc')
    dedicated_title = data.get('dedicated_title')
    dedicated_document_id = data.get('dedicated_document_id')

    try:
        result = generate_google_patents_query(
            structured_search_conditions=structured_search_conditions,
            inventors=inventors,
            assignees=assignees,
            after_date=after_date,
            after_date_type=after_date_type,
            before_date=before_date,
            before_date_type=before_date_type,
            patent_offices=patent_offices_list,
            languages=languages_list, # CHANGED: Pass the list
            status=status,
            patent_type=patent_type,
            litigation=litigation,
            dedicated_cpc=dedicated_cpc,
            dedicated_title=dedicated_title,
            dedicated_document_id=dedicated_document_id
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error generating Google query: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred processing the query."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)