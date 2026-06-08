import threading
from fastapi import APIRouter
from backend.pipeline.incremental.run import run_pipeline

router = APIRouter()

pipeline_status = {
    "running": False,
    "result": None,
    "error": None
}


def background_pipeline():
    global pipeline_status

    pipeline_status["running"] = True
    pipeline_status["error"] = None

    try:
        inserted_count, elapsed = run_pipeline()

        pipeline_status["result"] = {
            "number_of_data_newly_added": inserted_count,
            "time_taken_seconds": round(elapsed, 2)
        }

    except Exception as e:
        pipeline_status["error"] = str(e)

    finally:
        pipeline_status["running"] = False


@router.get("/")
def start_pipeline():

    if pipeline_status["running"]:
        return {
            "message": "Pipeline already running",
            "data": {
                "status": "running"
            }
        }

    pipeline_status["result"] = None
    pipeline_status["error"] = None

    thread = threading.Thread(
        target=background_pipeline,
        daemon=True
    )
    thread.start()

    return {
        "message": "Pipeline started in background",
        "data": {
            "status": "running"
        }
    }


@router.get("/status")
def pipeline_result():

    return {
        "running": pipeline_status["running"],
        "result": pipeline_status["result"],
        "error": pipeline_status["error"]
    }