# processing/validation.py
import logging
import great_expectations as gx

logger = logging.getLogger(__name__)


def run_validation():
    context = gx.get_context(context_root_dir="/app/gx")

    result = context.run_checkpoint(
        checkpoint_name="prices_checkpoint",
        batch_request={
            "runtime_parameters": {
                "query": "SELECT * FROM prices"
            },
            "batch_identifiers": {
                "default_identifier_name": "prices_full_table"
            }
        }
    )

    if not result.success:
        raise ValueError("GE validation failed")

    return {"passed": True}
