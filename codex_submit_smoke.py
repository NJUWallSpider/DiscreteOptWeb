import os
import time

from django.core.files import File

from competitions.models import CompetitionCreationTaskStatus, CompetitionParticipant, Submission
from competitions.tasks import unpack_competition
from datasets.models import Data
from profiles.models import User


COMPETITION_ZIP = "/app/tests/test_files/competitions/competition_v2_wheat_code.zip"
SUBMISSION_ZIP = "/app/tests/test_files/submissions/submission_v2_wheat_code.zip"


def save_data_file(data, path):
    with open(path, "rb") as handle:
        data.data_file.save(os.path.basename(path), File(handle), save=True)


def main():
    admin = User.objects.get(username="admin")
    stamp = time.strftime("%Y%m%d-%H%M%S")

    bundle = Data.objects.create(
        created_by=admin,
        type=Data.COMPETITION_BUNDLE,
        name=f"Codex smoke competition bundle {stamp}",
        description="Temporary smoke-test competition uploaded by Codex.",
        file_size=os.path.getsize(COMPETITION_ZIP),
    )
    save_data_file(bundle, COMPETITION_ZIP)

    status = CompetitionCreationTaskStatus.objects.create(
        created_by=admin,
        dataset=bundle,
        status=CompetitionCreationTaskStatus.STARTING,
    )
    print(f"created_status={status.pk}")

    unpack_competition(status.pk)
    status.refresh_from_db()
    print(f"unpack_status={status.status}")
    if status.status != CompetitionCreationTaskStatus.FINISHED:
        print(f"unpack_details={status.details}")
        return 2

    competition = status.resulting_competition
    phase = competition.phases.order_by("index", "pk").first()
    tasks = list(phase.tasks.all())
    if not phase or not tasks:
        print("missing_phase_or_tasks")
        return 3

    participant, _ = CompetitionParticipant.objects.get_or_create(
        competition=competition,
        user=admin,
        defaults={"status": CompetitionParticipant.APPROVED},
    )
    participant.status = CompetitionParticipant.APPROVED
    participant.save(update_fields=["status"])

    submission_data = Data.objects.create(
        created_by=admin,
        competition=competition,
        type=Data.SUBMISSION,
        name=f"Codex smoke submission {stamp}",
        description="Temporary smoke-test submission uploaded by Codex.",
        file_size=os.path.getsize(SUBMISSION_ZIP),
    )
    save_data_file(submission_data, SUBMISSION_ZIP)

    submission = Submission(
        owner=admin,
        phase=phase,
        data=submission_data,
        participant=participant,
        queue=competition.queue,
    )
    submission.save(ignore_submission_limit=True)
    submission.start(tasks=tasks)

    print(f"competition_id={competition.pk}")
    print(f"competition_title={competition.title}")
    print(f"phase_id={phase.pk}")
    print(f"task_ids={[task.pk for task in tasks]}")
    print(f"submission_id={submission.pk}")

    terminal = {Submission.FINISHED, Submission.FAILED, Submission.CANCELLED}
    for _ in range(90):
        submission.refresh_from_db()
        children = list(submission.children.order_by("pk").values_list("pk", "status", "status_details"))
        print(
            f"poll parent={submission.status} details={submission.status_details!r} "
            f"children={children}"
        )
        if submission.status in terminal:
            return 0 if submission.status == Submission.FINISHED else 4
        if children and all(child_status in terminal for _, child_status, _ in children):
            return 0 if all(child_status == Submission.FINISHED for _, child_status, _ in children) else 4
        time.sleep(2)

    print("timeout_waiting_for_submission")
    return 5


raise SystemExit(main())
