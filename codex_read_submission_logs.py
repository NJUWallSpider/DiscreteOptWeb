from competitions.models import SubmissionDetails


for detail in SubmissionDetails.objects.filter(submission_id=85).order_by("id"):
    print(f"--- {detail.name} {detail.data_file.name}")
    try:
        content = detail.data_file.read().decode("utf-8", errors="replace")
    except Exception as exc:
        content = f"READ_ERROR {exc!r}"
    print(content[-4000:])
