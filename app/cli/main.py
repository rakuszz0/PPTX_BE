from __future__ import annotations
from typing import Optional
import asyncio
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.database.session import init_db


def _ensure_dirs() -> None:
    for d in ["data", "cache", "output", "assets"]:
        Path(d).mkdir(parents=True, exist_ok=True)


async def _async_demo(url: str, module: int, min_slides: int, max_slides: int, theme: str) -> int:
    from uuid import uuid4
    from datetime import UTC, datetime

    from app.database.models import Course, Job
    from app.database.session import get_session
    from app.services.pipeline.pipeline_runner import run_job_pipeline

    init_db()
    sess = get_session()
    try:
        course_id = f"course_demo_{uuid4().hex[:10]}"
        course = Course(
            id=course_id,
            title="Kepatuhan Regulasi untuk Perangkat Medis",
            source_url=url,
            project_id=None,
            status="CREATED",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        sess.add(course)
        sess.commit()

        job_id = f"job_demo_{uuid4().hex[:10]}"
        job = Job(
            id=job_id,
            course_id=course_id,
            module_id=None,
            status="PENDING",
            stage="init",
            progress=0,
            current_slide=0,
            total_slides=0,
            config={
                "max_slides": max_slides,
                "min_slides": min_slides,
                "theme": theme,
            },
            created_by="cli",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        sess.add(job)
        sess.commit()
    finally:
        sess.close()

    await run_job_pipeline(job_id)

    from sqlalchemy import func
    from app.database.session import get_session
    from app.database.models import Job, Presentation, QAResult, Slide
    sess2 = get_session()
    try:
        job = sess2.query(Job).filter(Job.id == job_id).first()
        print(f"\n=== JOB FINAL STATUS ===")
        print(f"job_id      : {job_id}")
        print(f"status      : {job.status if job else 'UNKNOWN'}")
        print(f"progress    : {job.progress if job else '?'}")
        print(f"stage       : {job.stage if job else '?'}")
        if job and job.error_message:
            print(f"error       : {job.error_message}")

        pres = sess2.query(Presentation).filter(Presentation.course_id == course_id).first()
        slide_count = 0
        if pres:
            slide_count = sess2.query(func.count(Slide.id)).filter(Slide.presentation_id == pres.id).scalar() or 0
            print(f"\n=== PRESENTATION ===")
            print(f"id          : {pres.id}")
            print(f"title       : {pres.title}")
            print(f"version     : {pres.version}")
            print(f"slides (db) : {slide_count}")
            print(f"qa_score    : {pres.qa_score}")
            print(f"output_path : {pres.output_path}")
            if pres.output_path and Path(pres.output_path).exists():
                size = Path(pres.output_path).stat().st_size
                print(f"pptx_size   : {size:,} bytes ({size/1024:.1f} KB)")
        qa = sess2.query(QAResult).filter(QAResult.presentation_id == pres.id if pres else None).order_by(QAResult.created_at.desc()).first()
        if qa:
            print(f"\n=== QA RESULTS ===")
            print(f"overall     : {qa.overall_score}/100  {'PASS' if qa.passed else 'FAIL'}")
            for name, val in [
                ("content", qa.content_score), ("educational", qa.educational_score),
                ("visual", qa.visual_score), ("readability", qa.readability_score),
                ("consistency", qa.consistency_score), ("editability", qa.editability_score),
                ("technical", qa.technical_score)]:
                if val is not None:
                    print(f"  {name:<14}: {val}")
            if qa.issues:
                print(f"issues      :")
                for iss in qa.issues[:8]:
                    print(f"  - [{iss.get('severity','?')}] {iss.get('message','?')}")
    finally:
        sess2.close()
    return 0


def cmd_demo(args) -> int:
    url = args.url
    module = args.module
    min_slides = args.min_slides
    max_slides = args.max_slides
    theme = args.theme
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    _ensure_dirs()
    return asyncio.run(_async_demo(url, module, min_slides, max_slides, theme))


def cmd_serve(args) -> int:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    _ensure_dirs()
    init_db()
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def cmd_resume(args) -> int:
    from app.services.pipeline.pipeline_runner import run_job_pipeline
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    _ensure_dirs()
    init_db()
    return asyncio.run(run_job_pipeline(args.job_id)) or 0


def cmd_health(args) -> int:
    from fastapi.testclient import TestClient
    from app.main import app
    setup_logging("WARNING")
    _ensure_dirs()
    init_db()
    with TestClient(app) as client:
        r = client.get("/api/v1/health")
        print(json.dumps(r.json(), indent=2))
    return 0


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(prog="wizape-presentation",
                                     description="Wizape Presentation Studio Backend")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_demo = sub.add_parser("demo", help="Run end-to-end demo pipeline (no server required)")
    p_demo.add_argument("--url", default="https://wizape.example/course/medical-regulasi/modules=10",
                        help="WIZAPE course URL")
    p_demo.add_argument("--module", type=int, default=1)
    p_demo.add_argument("--min-slides", type=int, default=10)
    p_demo.add_argument("--max-slides", type=int, default=12)
    p_demo.add_argument("--theme", default="medical_professional")
    p_demo.set_defaults(func=cmd_demo)

    p_serve = sub.add_parser("serve", help="Run FastAPI server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    p_resume = sub.add_parser("resume", help="Resume/retry a job")
    p_resume.add_argument("--job-id", required=True)
    p_resume.set_defaults(func=cmd_resume)

    p_health = sub.add_parser("health", help="Check app health")
    p_health.set_defaults(func=cmd_health)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
