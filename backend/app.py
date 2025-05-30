# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import for Google Patents (assuming it's still needed)
from google_generate_query import generate_google_patents_query 

# Import for USPTO Patents
from uspto_generate_query import generate_uspto_patents_query

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

@app.route('/api/generate-google-query', methods=['POST'])
def handle_generate_google_query():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Extract data for Google query
    structured_search_conditions = data.get('structured_search_conditions')
    inventors = data.get('inventors')
    assignees = data.get('assignees')
    after_date = data.get('after_date')
    after_date_type = data.get('after_date_type')
    before_date = data.get('before_date')
    before_date_type = data.get('before_date_type')
    patent_offices_list = data.get('patent_offices')
    languages_list = data.get('languages')
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
            languages=languages_list,
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
        return jsonify({"error": "An internal server error occurred processing the Google query."}), 500

@app.route('/api/generate-uspto-query', methods=['POST'])
def handle_generate_uspto_query():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided for USPTO query"}), 400

    # Extract data for USPTO query
    # Based on the signature of generate_uspto_patents_query:
    # conditions (list of dicts)
    # databases (list of strings)
    # combine_conditions_with (string, e.g., "AND", "OR")
    
    conditions = data.get('conditions') # This is the list of structured search conditions
    databases = data.get('databases')   # e.g., ["USPAT", "US-PGPUB"]
    combine_conditions_with = data.get('combine_conditions_with', 'AND') # Default to "AND" if not provided

    # Basic validation (can be expanded)
    if conditions is not None and not isinstance(conditions, list):
        return jsonify({"error": "'conditions' must be a list"}), 400
    if databases is not None and not isinstance(databases, list):
        return jsonify({"error": "'databases' must be a list"}), 400
    if not isinstance(combine_conditions_with, str) or \
       combine_conditions_with.upper() not in ["AND", "OR"]:
        return jsonify({"error": "'combine_conditions_with' must be 'AND' or 'OR'"}), 400
        
    try:
        result = generate_uspto_patents_query(
            conditions=conditions,
            databases=databases,
            combine_conditions_with=combine_conditions_with.upper() # Ensure it's uppercase
        )
        return jsonify(result)
    except ValueError as e: # Catch specific ValueErrors if your function raises them
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error generating USPTO query: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred processing the USPTO query."}), 500

if __name__ == '__main__':
    # Ensure debug is False in production
    app.run(debug=True, port=5001)