"""Utility functions used in tech team app"""

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any
from unittest.mock import Mock, patch

from django.contrib.auth.models import User

from ..cases.models import Sector
from ..comments.models import Comment
from ..common.models import ZENDESK_URL_PREFIX, Boolean
from ..common.utils import extract_domain_from_url
from ..detailed.models import DetailedCase, DetailedCaseHistory
from ..mobile.models import (
    EventHistory,
    MobileCase,
    MobileCaseHistory,
    MobileContact,
    MobileZendeskTicket,
)
from ..mobile.utils import record_mobile_model_create_event
from ..notifications.models import Task

logger = logging.getLogger(__name__)

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
    if " " in date:  # Multiple dates in string
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
    mobile_case: MobileCase, created_by: User, note: str
) -> None:
    mobile_case_history: MobileCaseHistory = MobileCaseHistory.objects.create(
        mobile_case=mobile_case,
        event_type=MobileCaseHistory.EventType.NOTE,
        value=note,
        created_by=created_by,
    )
    record_mobile_model_create_event(
        user=created_by, model_object=mobile_case_history, mobile_case=mobile_case
    )


def create_mobile_case_from_dict(
    row: dict[str, Any],
    default_user: User,
    auditors: dict[str, User],
    sectors: dict[str, Sector],
) -> None:
    """User dictionary date (from csv) to create mobile Case"""
    legacy_case_number: str = row["Record "]
    case_identifier = f"#M-{legacy_case_number[1:]}"
    app_os: str = row["Type"]
    url: str = validate_url(row["URL"])
    if app_os == "Android":
        mobile_case: MobileCase = MobileCase.objects.filter(
            case_identifier=case_identifier
        ).first()
        if mobile_case is not None:
            mobile_case.android_app_name = row["App name"]
            mobile_case.android_app_store_url = url
            mobile_case.save()
            return
    first_contact_date: str = get_datetime_from_string(
        row["First contact date"]
    )  # dd/mm/yyyy
    if first_contact_date:
        created: datetime = first_contact_date
    else:
        created: datetime = datetime.now().astimezone(timezone.utc)
    last_date: str = row["Date decision email sent"]  # dd/mm/yyyy
    updated: datetime = get_datetime_from_string(last_date)
    if updated is None:
        updated: datetime = created
    auditor: User = auditors.get(row["Auditor"], default_user)
    qa_auditors: str = row["Report checked by"]
    if " " in qa_auditors:
        qa_auditor: User = auditors.get(qa_auditors.split(" ")[0], default_user)
    else:
        qa_auditor: User = auditors.get(qa_auditors, default_user)
    feedback_survey_sent: str = row["Feedback survey sent "]
    is_feedback_requested: Boolean = (
        Boolean.YES if feedback_survey_sent == "Yes" else Boolean.NO
    )
    status: str = MAP_CASE_STATUS.get(row["Status"], MobileCase.Status.UNASSIGNED)

    with patch("django.utils.timezone.now", Mock(return_value=created)):
        mobile_case: MobileCase = MobileCase.objects.create(
            test_type=MobileCase.TestType.MOBILE,
            created_by_id=default_user.id,
            updated=updated,
            ios_app_name=row["App name"],
            ios_app_store_url=url,
            domain=extract_domain_from_url(url),
            auditor_id=auditor.id,
            organisation_name=row["Organisation name"],
            # website_name=row["Website"],
            enforcement_body=row["Enforcement body"].lower(),
            is_complaint=row["Is it a complaint?"].lower(),
            equality_body_report_url=validate_url(row["Public link to report PDF"]),
            reviewer=qa_auditor,
            report_sent_date=get_datetime_from_string(row["Report sent on"]),
            report_acknowledged_date=get_datetime_from_string(
                row["Report acknowledged"]
            ),
            twelve_week_deadline_date=get_datetime_from_string(
                row["Followup date - 12 week deadline"]
            ),
            retest_statement_compliance_state=MAP_STATEMENT_COMPLIANCE.get(
                row["Accessibility Statement Decision"].lower(),
                DetailedCase.StatementCompliance.UNKNOWN,
            ),
            retest_statement_compliance_information=row[
                "Notes on accessibility statement"
            ],
            retest_disproportionate_burden_information=row[
                "Disproportionate Burden Notes"
            ],
            recommendation_for_enforcement=MAP_ENFORCEMENT_RECOMMENDATION.get(
                row["Enforcement Recommendation"],
                DetailedCase.RecommendationForEnforcement.UNKNOWN,
            ),
            retest_start_date=get_datetime_from_string(row["Retest date"]),
            recommendation_decision_sent_date=get_datetime_from_string(
                row["Date decision email sent"]
            ),
            enforcement_body_sent_date=get_datetime_from_string(
                row["Date sent to enforcement body"]
            ),
            enforcement_body_closed_case_state=MAP_ENFORCEMENT_BODY_CLOSED_CASE.get(
                row["Active case with enforcement body?"],
                DetailedCase.StatementCompliance.UNKNOWN,
            ),
            is_feedback_requested=is_feedback_requested,
            contact_information_request_start_date=get_datetime_from_string(
                row["First contact date"]
            ),
            psb_location=MAP_PSB_LOCATION.get(
                row["Public sector body location"], DetailedCase.PsbLocation.UNKNOWN
            ),
            sector=sectors[row["Sector"]],
            retest_disproportionate_burden_claim=MAP_DISPROPORTIONATE_BURDEN_CLAIM.get(
                row["Disproportionate Burden Claimed?"],
                DetailedCase.DisproportionateBurden.NOT_CHECKED,
            ),
            psb_progress_info=row["Summary of progress made / response from PSB"],
            recommendation_info=row["Enforcement Recommendation Notes"],
            parental_organisation_name=row["Parent org (if relevant)"],
            status=status,
            case_folder_url=row["Link to case folder"],
            initial_test_start_date=get_datetime_from_string(row["Test start date"]),
            initial_test_end_date=get_datetime_from_string(row["Test end date"]),
            initial_total_number_of_issues=get_number_from_string(
                row["Total issues (excluding best practice)"]
            ),
            initial_total_number_of_pages=get_number_from_string(
                row["Number of pages tested"]
            ),
            retest_total_number_of_issues=get_number_from_string(
                row["Number of issues on closure"]
            ),
            initial_website_compliance_state=MAP_WEBSITE_COMPLIANCE.get(
                row["Initial app compliance"].lower(),
                DetailedCase.WebsiteCompliance.UNKNOWN,
            ),
            initial_statement_compliance_state=MAP_STATEMENT_COMPLIANCE.get(
                row["Initial statement compliance"].lower(),
                DetailedCase.StatementCompliance.UNKNOWN,
            ),
            is_case_added_to_stats=(
                Boolean.YES
                if row["Added to stats tab (formula)"] == "Yes"
                else Boolean.NO
            ),
        )

        mobile_case.case_identifier = case_identifier
        mobile_case.save()

        MobileCaseHistory.objects.create(
            mobile_case_id=mobile_case.id,
            event_type=MobileCaseHistory.EventType.STATUS,
            value="Imported from spreadsheet",
            created_by=auditor,
        )

        if " " in qa_auditors:
            add_note_to_mobile_history(
                mobile_case=mobile_case,
                created_by=auditor,
                note=f"All legacy QA auditors: {qa_auditors}",
            )

        if feedback_survey_sent and feedback_survey_sent != "Yes":
            add_note_to_mobile_history(
                mobile_case=mobile_case,
                created_by=auditor,
                note=f"Feedback survey sent from imported spreadsheet:\n\n{feedback_survey_sent}",
            )

        if row["Contact name"] or row["Job title"] or row["Contact detail"]:
            contact: MobileContact = MobileContact.objects.create(
                mobile_case=mobile_case,
                name=row["Contact name"],
                job_title=row["Job title"],
                contact_details=row["Contact detail"],
                created_by=auditor,
            )
            contact.save()

        zendesk_urls: str = row["Zendesk ticket"]
        for zendesk_url in zendesk_urls.split():
            if zendesk_url.startswith(ZENDESK_URL_PREFIX):
                MobileZendeskTicket.objects.create(
                    mobile_case=mobile_case,
                    url=zendesk_url,
                    summary="From imported spreadsheet",
                )

        add_note_to_mobile_history(
            mobile_case=mobile_case,
            created_by=auditor,
            note=f"Legacy record id: {legacy_case_number}",
        )


def import_mobile_cases_csv(csv_data: str) -> None:
    default_user = User.objects.filter(id=DEFAULT_USER_ID).first()
    if default_user is None:
        return
    try:
        auditors: dict[str, User] = {
            user.first_name: user for user in User.objects.all()
        }
    except User.DoesNotExist:  # Automated tests
        auditors = {}
    sectors: dict[str, Sector] = {
        sector.name: sector for sector in Sector.objects.all()
    }

    EventHistory.objects.all().delete()
    MobileCaseHistory.objects.all().delete()
    MobileContact.objects.all().delete()
    MobileZendeskTicket.objects.all().delete()
    for mobile_case in MobileCase.objects.all():
        Task.objects.filter(base_case=mobile_case).delete()
        Comment.objects.filter(base_case=mobile_case).delete()
    MobileCase.objects.all().delete()

    reader: Any = csv.DictReader(io.StringIO(csv_data))
    for row in reader:
        if row["Enforcement body"] == "":
            continue
        create_mobile_case_from_dict(
            row=row, default_user=default_user, auditors=auditors, sectors=sectors
        )


def import_trello_comments(csv_data: str, reset_data: bool = False) -> None:
    comment_fullname_to_user: dict[str, User] = {
        f"{user.first_name.lower()}.{user.last_name.lower()}": user
        for user in User.objects.all()
    }
    default_user: User = User.objects.get(id=DEFAULT_USER_ID)
    if reset_data:
        MobileCaseHistory.objects.filter(label=TRELLO_COMMENT_LABEL).delete()
        MobileCaseHistory.objects.filter(label=TRELLO_DESCRIPTION_LABEL).delete()
    card_descriptions: dict[DetailedCase, str] = {}
    reader: Any = csv.DictReader(io.StringIO(csv_data))
    for row in reader:
        case_no: str = row["case_no"]
        if case_no == "":
            continue
        if row["case_no"].startswith("M"):
            case_identifier: str = f"#M-{case_no[1:]}"
            try:
                mobile_case: MobileCase = MobileCase.objects.get(
                    case_identifier=case_identifier
                )
                card_descriptions[mobile_case] = row["card_description"]
                comment_time: datetime = datetime.strptime(
                    row["comment_date"], "%Y-%m-%dT%H:%M:%S.%fZ"
                ).replace(tzinfo=timezone.utc)
                with patch(
                    "django.utils.timezone.now", Mock(return_value=comment_time)
                ):
                    MobileCaseHistory.objects.create(
                        mobile_case=mobile_case,
                        event_type=MobileCaseHistory.EventType.NOTE,
                        value=row["comment_text"].replace(' "\u200c")', ")"),
                        label=TRELLO_COMMENT_LABEL,
                        created_by=comment_fullname_to_user.get(
                            row["comment_fullname"].lower().replace(" ", "."),
                            default_user,
                        ),
                    )
            except MobileCase.DoesNotExist:
                logger.warning("MobileCase not found: %s", case_identifier)

    # Add description text
    for mobile_case, description_text in card_descriptions.items():
        DetailedCaseHistory.objects.create(
            mobile_case=mobile_case,
            event_type=DetailedCaseHistory.EventType.NOTE,
            value=description_text.replace(' "\u200c")', ")"),
            label=TRELLO_DESCRIPTION_LABEL,
            created_by=default_user,
        )
