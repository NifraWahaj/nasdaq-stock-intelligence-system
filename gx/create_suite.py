# gx/create_suite.py
import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest
import json

def create_nasdaq_suite():
    """
    Core logic to build and save the expectation suite.
    """
    context = gx.get_context(context_root_dir="/app/gx")
    
    # Creates new or refreshes existing suite
    context.add_or_update_expectation_suite(expectation_suite_name="prices_suite")

    batch_request = RuntimeBatchRequest(
        datasource_name="nasdaq_postgres",
        data_connector_name="default_runtime_data_connector",
        data_asset_name="prices",
        runtime_parameters={
            "query": "SELECT * FROM prices LIMIT 100" # Limit for speed during init
        },
        batch_identifiers={
            "default_identifier_name": "initial_suite_build"
        }
    )

    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name="prices_suite"
    )

    # --- DEFINE EXPECTATIONS ---
    validator.expect_column_values_to_not_be_null("close")
    
    # Save the suite to the JSON file
    validator.save_expectation_suite(discard_failed_expectations=False)
    
    print("Expectation suite 'prices_suite' saved successfully.")
    return True

if __name__ == "__main__`":
    # This only runs if you call the script directly via CLI
    create_nasdaq_suite()