import re

with open("backend/tasks/audit_tasks.py", "r") as f:
    content = f.read()

# 1. Replace @celery.task(bind=True) to include max_retries
content = content.replace(
    "@celery.task(bind=True)",
    "@celery.task(bind=True, max_retries=3, default_retry_delay=60)"
)

# 2. Add structured logger import and replace logging
content = content.replace(
    "import logging",
    "from backend.observability.structured_logger import get_logger"
)
content = content.replace(
    "logger = logging.getLogger(__name__)",
    "logger = get_logger(__name__)"
)

# 3. Add exception handling to execute_audit
old_audit_return = """    result = (

        audit_service
        .execute_full_audit(

            github_owner=
                owner,

            github_repo=
                repo,

            provider=
                provider,

            srs_path=
                srs_path,

            audit_run_id=
                self.request.id
        )
    )

    return result"""

new_audit_return = """    try:
        result = (
            audit_service
            .execute_full_audit(
                github_owner=owner,
                github_repo=repo,
                provider=provider,
                srs_path=srs_path,
                audit_run_id=self.request.id
            )
        )
        return result
    except Exception as e:
        from backend.observability.structured_logger import get_logger
        lgr = get_logger(__name__)
        lgr.error("execute_audit_failed", error=str(e), exc_info=True)
        raise self.retry(exc=e)"""

content = content.replace(old_audit_return, new_audit_return)

# 4. _mark_audit_failed rollback
old_db_err = """        db.commit()
    except Exception as db_err:
        logger.error(f"Failed to mark audit failed after error '{error_message}': {db_err}")
    finally:
        db.close()"""

new_db_err = """        db.commit()
    except Exception as db_err:
        db.rollback()
        logger.error("mark_audit_failed_error", original_error=error_message, db_error=str(db_err))
    finally:
        db.close()"""

content = content.replace(old_db_err, new_db_err)

# 5. db_persist.commit() error
old_db_persist_err = """            db_persist.commit()
        except Exception as db_err:
            logger.error(f"DB persistence error in delay analysis task: {db_err}")
            db_persist.rollback()
        finally:
            db_persist.close()"""

new_db_persist_err = """            db_persist.commit()
        except Exception as db_err:
            logger.error("db_persistence_error", error=str(db_err))
            db_persist.rollback()
            raise
        finally:
            db_persist.close()"""

content = content.replace(old_db_persist_err, new_db_persist_err)

# 6. delay analysis failed error
old_delay_failed = """    except Exception as e:
        logger.error(f"Delay analysis failed: {e}")
        import traceback
        traceback.print_exc()
        _mark_audit_failed(session_id, str(e))
        return {"status": "FAILED", "error": str(e), "error_type": "Exception"}"""

new_delay_failed = """    except Exception as e:
        logger.error("delay_analysis_failed", error=str(e), exc_info=True)
        _mark_audit_failed(session_id, str(e))
        
        if not isinstance(e, InsufficientDataError):
            try:
                raise self.retry(exc=e)
            except self.MaxRetriesExceededError:
                pass
                
        return {"status": "FAILED", "error": str(e), "error_type": "Exception"}"""

content = content.replace(old_delay_failed, new_delay_failed)

with open("backend/tasks/audit_tasks.py", "w") as f:
    f.write(content)

print("Patched audit_tasks.py successfully!")
