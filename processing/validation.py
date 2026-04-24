# processing/validation.py
import logging
from unittest import result
import great_expectations as gx

logger = logging.getLogger(__name__)

"""
Great Expectations validation for prices table.
Fails pipeline if expectations are not met.
"""

def run_validation():
    """
    Great Expectations validation for prices table.
    Fails pipeline if expectations are not met.
    """
    logger.info("Running GE validation checkpoint on prices table")

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
        failed = [
            r.expectation_config.expectation_type
            for vr in result.run_results.values()
            for r in vr["validation_result"].results
            if not r.success
        ]
        logger.error(f"GE validation failed. Failed checks: {failed}")
        raise ValueError(f"GE validation failed: {failed}")

    logger.info("GE validation passed — all expectations met")
    return {"passed": True}



    