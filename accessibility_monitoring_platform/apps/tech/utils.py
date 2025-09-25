"""Utility functions used in tech team app"""

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any
from unittest.mock import Mock, patch

from django.contrib.auth.models import User

# from ..cases.models import Sector
# from ..comments.models import Comment
# from ..common.models import Boolean
from ..common.utils import extract_domain_from_url
from ..detailed.models import DetailedCase, DetailedCaseHistory
from ..mobile.models import EventHistory, MobileCase, MobileCaseHistory
from ..mobile.utils import record_mobile_model_create_event

# from ..notifications.models import Task

logger = logging.getLogger(__name__)

ZENDESK_URL_PREFIX: str = "https://govuk.zendesk.com/agent/tickets/"
MAP_WEBSITE_COMPLIANCE: dict[str, str] = {
    "not compliant": DetailedCase.WebsiteCompliance.NOT,
    "": DetailedCase.WebsiteCompliance.UNKNOWN,
    "other": DetailedCase.WebsiteCompliance.UNKNOWN,
    "partially compliant": DetailedCase.WebsiteCompliance.PARTIALLY,
}
MAP_STATEMENT_COMPLIANCE: dict[str, str] = {
    "not compliant": DetailedCase.StatementCompliance.NOT_COMPLIANT,
    "": DetailedCase.StatementCompliance.UNKNOWN,
    "other": DetailedCase.StatementCompliance.UNKNOWN,
    "compliant": DetailedCase.StatementCompliance.COMPLIANT,
    "no statement": DetailedCase.StatementCompliance.NO_STATEMENT,
    "not found": DetailedCase.StatementCompliance.NO_STATEMENT,
}
MAP_ENFORCEMENT_RECOMMENDATION: dict[str, str] = {
    "No further action": DetailedCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
    "For enforcement consideration": DetailedCase.RecommendationForEnforcement.OTHER,
    "": DetailedCase.RecommendationForEnforcement.UNKNOWN,
}
MAP_ENFORCEMENT_BODY_CLOSED_CASE: dict[str, str] = {
    "No": DetailedCase.EnforcementBodyClosedCase.YES,
    "Yes": DetailedCase.EnforcementBodyClosedCase.IN_PROGRESS,
    "": DetailedCase.EnforcementBodyClosedCase.NO,
}
MAP_PSB_LOCATION: dict[str, str] = {
    "England": DetailedCase.PsbLocation.ENGLAND,
    "Scotland": DetailedCase.PsbLocation.SCOTLAND,
    "Wales": DetailedCase.PsbLocation.WALES,
    "Northern Ireland": DetailedCase.PsbLocation.NI,
    "UK-wide": DetailedCase.PsbLocation.UK,
    "Unknown": DetailedCase.PsbLocation.UNKNOWN,
}
MAP_DISPROPORTIONATE_BURDEN_CLAIM: dict[str, str] = {
    "Claim with no assessment": DetailedCase.DisproportionateBurden.NO_ASSESSMENT,
    "Claim with assessment": DetailedCase.DisproportionateBurden.ASSESSMENT,
    "No claim": DetailedCase.DisproportionateBurden.NO_CLAIM,
    "No statement": DetailedCase.DisproportionateBurden.NO_STATEMENT,
    "Not checked": DetailedCase.DisproportionateBurden.NOT_CHECKED,
}
MAP_CASE_STATUS: dict[str, str] = {
    "Case closed and sent to equality body": DetailedCase.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY,
    "Report in progress": DetailedCase.Status.REPORT_IN_PROGRESS,
    "Report acknowledged waiting for 12-week deadline": DetailedCase.Status.AWAITING_12_WEEK_DEADLINE,
    "Requested update at 12 weeks": DetailedCase.Status.REQUESTED_12_WEEK_UPDATE,
    "Reviewing changes": DetailedCase.Status.REVIEWING_CHANGES,
    "Complete": DetailedCase.Status.COMPLETE,
}
DEFAULT_USER_ID: int = 3
TRELLO_COMMENT_LABEL: str = "Imported from Trello"
TRELLO_DESCRIPTION_LABEL: str = "Description imported from Trello"


def get_datetime_from_string(date: str) -> datetime | None:
    if len(date) < 5:
        return None
    if date[0].isdigit():
        # dd/mm/yyyy
        day, month, year = date.split("/")
        day: int = int(day)
        month: int = int(month)
        year: int = int(year)
        if year < 100:
            year += 2000
        return datetime(year, month, day, tzinfo=timezone.utc)
    # mmm yyyy
    return datetime.strptime(f"1 {date}", "%d %b %Y").replace(tzinfo=timezone.utc)


def get_number_from_string(number: str) -> int | None:
    if number in ["", "-"]:
        return None
    if number.isdigit():
        return int(number)
    return None


def validate_url(url: str) -> str:
    if url.startswith("http"):
        return url
    return ""


def add_note_to_mobile_history(
    mobile_case: MobileCase, created: datetime, created_by: User, note: str
) -> None:
    mobile_case_history: MobileCaseHistory = MobileCaseHistory.objects.create(
        mobile_case=mobile_case,
        event_type=MobileCaseHistory.EventType.NOTE,
        value=note,
        created_by=created_by,
    )
    mobile_case_history.created = created
    mobile_case_history.save()
    record_mobile_model_create_event(
        user=created_by, model_object=mobile_case_history, mobile_case=mobile_case
    )


def create_mobile_case_from_dict(
    row: dict[str, Any], default_user: User, auditors: dict[str, User]
) -> None:
    """User dictionary date (from csv) to create mobile Case"""
    case_number: int = int(row["Record "][1:])
    app_os: str = row["Type"].lower()
    created: datetime = get_datetime_from_string(row["First contact date"])
    last_date: str = get_datetime_from_string(row["Date decision email sent"])
    if last_date is not None:
        updated: datetime = last_date
    else:
        updated: datetime = created
    auditor: User = auditors.get(row["Auditor"], default_user)
    url: str = validate_url(row["URL"])
    enforcement_body: str = row["Enforcement body"].lower()
    is_complaint: str = row["Is it a complaint?"].lower()
    mobile_case: MobileCase = MobileCase.objects.create(
        test_type=MobileCase.TestType.MOBILE,
        created_by_id=default_user.id,
        updated=updated,
        auditor_id=auditor.id,
        app_name=row["App name"],
        app_store_url=url,
        domain=extract_domain_from_url(url),
        app_os=app_os,
        enforcement_body=enforcement_body,
        is_complaint=is_complaint,
        case_folder_url=row["Link to case folder"],
        initial_test_start_date=get_datetime_from_string(row["Test start date"]),
        initial_test_end_date=get_datetime_from_string(row["Test end date"]),
    )
    mobile_case.created = created
    mobile_case.case_number = case_number
    mobile_case.case_identifier = f"#M-{case_number}"
    mobile_case.save()
    for column_name in [
        "Summary of progress made / response from PSB",
    ]:
        if row[column_name]:
            add_note_to_mobile_history(
                mobile_case=mobile_case,
                created=updated,
                created_by=auditor,
                note=f"Legacy {column_name}:\n\n{row[column_name]}",
            )


def import_mobile_cases_csv(csv_data: str) -> None:
    default_user = User.objects.filter(first_name="Paul").first()
    if default_user is None:
        return
    try:
        auditors: dict[str, User] = {
            first_name: User.objects.get(first_name=first_name)
            for first_name in ["Andrew", "Katherine", "Kelly"]
        }
    except User.DoesNotExist:  # Automated tests
        auditors = {}

    EventHistory.objects.all().delete()
    MobileCaseHistory.objects.all().delete()
    MobileCase.objects.all().delete()

    reader: Any = csv.DictReader(io.StringIO(csv_data))
    for row in reader:
        if row["Enforcement body"] == "":
            continue
        create_mobile_case_from_dict(
            row=row, default_user=default_user, auditors=auditors
        )


def import_trello_comments(csv_data: str, reset_data: bool = False) -> None:
    comment_fullname_to_user: dict[str, User] = {
        f"{user.first_name} {user.last_name}": user for user in User.objects.all()
    }
    default_user: User = User.objects.get(id=DEFAULT_USER_ID)
    if reset_data:
        DetailedCaseHistory.objects.filter(label=TRELLO_COMMENT_LABEL).delete()
        DetailedCaseHistory.objects.filter(label=TRELLO_DESCRIPTION_LABEL).delete()
    card_descriptions: dict[DetailedCase, str] = {}
    reader: Any = csv.DictReader(io.StringIO(csv_data))
    for row in reader:
        case_no: str = row["case_no"]
        if case_no == "":
            continue
        if row["case_no"].startswith("D"):
            case_identifier: str = f"#D-{case_no[1:]}"
            try:
                detailed_case: DetailedCase = DetailedCase.objects.get(
                    case_identifier=case_identifier
                )
                card_descriptions[detailed_case] = row["card_description"]
                comment_time: datetime = datetime.strptime(
                    row["comment_date"], "%Y-%m-%dT%H:%M:%S.%fZ"
                ).replace(tzinfo=timezone.utc)
                with patch(
                    "django.utils.timezone.now", Mock(return_value=comment_time)
                ):
                    DetailedCaseHistory.objects.create(
                        detailed_case=detailed_case,
                        event_type=DetailedCaseHistory.EventType.NOTE,
                        value=row["comment_text"].replace(' "\u200c")', ")"),
                        label=TRELLO_COMMENT_LABEL,
                        created_by=comment_fullname_to_user.get(
                            row["comment_fullname"], default_user
                        ),
                    )
            except DetailedCase.DoesNotExist:
                logger.warning("DetailedCase not found: %s", case_identifier)

    # Add description text
    for detailed_case, description_text in card_descriptions.items():
        DetailedCaseHistory.objects.create(
            detailed_case=detailed_case,
            event_type=DetailedCaseHistory.EventType.NOTE,
            value=description_text.replace(' "\u200c")', ")"),
            label=TRELLO_DESCRIPTION_LABEL,
            created_by=default_user,
        )
