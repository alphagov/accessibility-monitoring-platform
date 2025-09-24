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
from ..common.models import Boolean
from ..common.utils import extract_domain_from_url
from ..detailed.models import (
    Contact,
    DetailedCase,
    DetailedCaseHistory,
    DetailedEventHistory,
    ZendeskTicket,
)
from ..detailed.utils import record_detailed_model_create_event
from ..mobile.models import EventHistory, MobileCase, MobileCaseHistory
from ..mobile.utils import record_mobile_model_create_event
from ..notifications.models import Task

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

COMMENT_FULLNAME_TO_USERNAME: dict[str, str] = {
    "amy.wallis": "amy.wallis@digital.cabinet-office.gov.uk",
    "Andrew Hick": "andrew.hick@digital.cabinet-office.gov.uk",
    "ChrisH": "chris.heathcote@digital.cabinet-office.gov.uk",
    "Eu-Hyung Han": "eu-hyung.han@digital.cabinet-office.gov.uk",
    # Jessica Eley's name missing from extract on 23 September 2024, came through as 'unknown'
    "unknown": "jessica.eley@digital.cabinet-office.gov.uk",
    "katherine.badger": "katherine.badger@digital.cabinet-office.gov.uk",
    "Keeley Robertson": "keeley.talbot@digital.cabinet-office.gov.uk",
    "Kelly Clarkson": "kelly.clarkson@digital.cabinet-office.gov.uk",
    "nesha.russo": "nesha.russo@digital.cabinet-office.gov.uk",
    "Nicole Tinti": "nicole.tinti@digital.cabinet-office.gov.uk",
}
TRELLO_COMMENT_LABEL: str = "Imported from Trello"
TRELLO_DESCRIPTION_LABEL: str = "Description imported from Trello"


def add_note_to_history(
    detailed_case: DetailedCase, created: datetime, created_by: User, note: str
) -> None:
    with patch("django.utils.timezone.now", Mock(return_value=created)):
        detailed_case_history: DetailedCaseHistory = DetailedCaseHistory.objects.create(
            detailed_case=detailed_case,
            event_type=DetailedCaseHistory.EventType.NOTE,
            value=note,
            created_by=created_by,
        )
    record_detailed_model_create_event(
        user=created_by, model_object=detailed_case_history, detailed_case=detailed_case
    )


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


def create_detailed_case_from_dict(
    row: dict[str, Any],
    default_user: User,
    auditors: dict[str, User],
    sectors: dict[str, Sector],
) -> None:
    original_record_number: str = row["Record "]
    case_number: int = int(original_record_number[1:])
    first_contact_date: str = get_datetime_from_string(
        row["First Contact Date"]
    )  # dd/mm/yyyy
    if first_contact_date:
        created: datetime = first_contact_date
    else:
        created: datetime = datetime.now().astimezone(timezone.utc)
    last_date: str = row["Date decision email sent"]  # dd/mm/yyyy
    last_updated: datetime = get_datetime_from_string(last_date)
    if last_updated is None:
        last_updated: datetime = created
    auditor: User = auditors.get(row["Auditor"], default_user)
    url: str = validate_url(row["URL"])
    qa_auditors: str = row["Report checked by"]
    if " " in qa_auditors:
        qa_auditor: User = auditors.get(qa_auditors.split(" ")[0], default_user)
    else:
        qa_auditor: User = auditors.get(qa_auditors, default_user)
    feedback_survey_sent: str = row["Feedback survey sent"]
    is_feedback_requested: Boolean = (
        Boolean.YES if feedback_survey_sent == "Yes" else Boolean.NO
    )
    status: str = MAP_CASE_STATUS.get(row["Status"], DetailedCase.Status.UNASSIGNED)

    with patch("django.utils.timezone.now", Mock(return_value=created)):
        detailed_case: DetailedCase = DetailedCase.objects.create(
            test_type=DetailedCase.TestType.DETAILED,
            created_by_id=default_user.id,
            updated=last_updated,
            auditor_id=auditor.id,
            home_page_url=url,
            domain=extract_domain_from_url(url=url),
            organisation_name=row["Organisation name"],
            website_name=row["Website"],
            enforcement_body=row["Enforcement body"].lower(),
            is_complaint=row["Is it a complaint?"].lower(),
            service_type=row["Type"].lower(),
            equality_body_report_url=validate_url(row["Public link to report PDF"]),
            reviewer=qa_auditor,
            report_sent_date=get_datetime_from_string(row["Report sent on"]),
            report_acknowledged_date=get_datetime_from_string(
                row["Report acknowledged"]
            ),
            twelve_week_deadline_date=get_datetime_from_string(
                row["Followup date - 12 week deadline"]
            ),
            retest_statement_compliance_state=MAP_STATEMENT_COMPLIANCE[
                row["Accessibility Statement Decision"].lower()
            ],
            retest_statement_compliance_information=row[
                "Notes on accessibility statement"
            ],
            retest_disproportionate_burden_information=row[
                "Disproportionate Burden Notes"
            ],
            recommendation_for_enforcement=MAP_ENFORCEMENT_RECOMMENDATION[
                row["Enforcement Recommendation"]
            ],
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
                row["First Contact Date"]
            ),
            psb_location=MAP_PSB_LOCATION[row["Public sector body location"]],
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
            initial_website_compliance_state=MAP_WEBSITE_COMPLIANCE[
                row["Initial site compliance"].lower()
            ],
            initial_statement_compliance_state=MAP_STATEMENT_COMPLIANCE[
                row["Initial statement compliance"].lower()
            ],
            is_case_added_to_stats=(
                Boolean.YES
                if row["Added to stats tab (formula)"] == "Yes"
                else Boolean.NO
            ),
        )
    detailed_case.case_number = case_number
    detailed_case.case_identifier = f"#D-{case_number}"
    detailed_case.save()

    DetailedCaseHistory.objects.create(
        detailed_case_id=detailed_case.id,
        event_type=DetailedCaseHistory.EventType.STATUS,
        value="Imported from spreadsheet",
        created_by=auditor,
    )

    if " " in qa_auditors:
        add_note_to_history(
            detailed_case=detailed_case,
            created=last_updated,
            created_by=auditor,
            note=f"All legacy QA auditors: {qa_auditors}",
        )

    for column_name in [
        "Related case notes (if applicable)",
    ]:
        if row[column_name]:
            add_note_to_history(
                detailed_case=detailed_case,
                created=last_updated,
                created_by=auditor,
                note=f"{column_name} from imported spreadsheet:\n\n{row[column_name]}",
            )

    if feedback_survey_sent and feedback_survey_sent != "Yes":
        add_note_to_history(
            detailed_case=detailed_case,
            created=last_updated,
            created_by=auditor,
            note=f"Feedback survey sent from imported spreadsheet:\n\n{feedback_survey_sent}",
        )

    if row["Contact name"] or row["Job title"] or row["Contact detail"]:
        contact: Contact = Contact.objects.create(
            detailed_case=detailed_case,
            name=row["Contact name"],
            job_title=row["Job title"],
            contact_details=row["Contact detail"],
            created_by=auditor,
        )
        contact.created = last_updated
        contact.save()

    zendesk_urls: str = row["Zendesk ticket"]
    for zendesk_url in zendesk_urls.split():
        if zendesk_url.startswith(ZENDESK_URL_PREFIX):
            ZendeskTicket.objects.create(
                detailed_case=detailed_case,
                url=zendesk_url,
                summary="From imported spreadsheet",
            )


def import_detailed_cases_csv(csv_data: str) -> None:
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
    sectors: dict[str, Sector] = {
        sector.name: sector for sector in Sector.objects.all()
    }

    Contact.objects.all().delete()
    ZendeskTicket.objects.all().delete()
    DetailedEventHistory.objects.all().delete()
    DetailedCaseHistory.objects.all().delete()
    for detailed_case in DetailedCase.objects.all():
        Task.objects.filter(base_case=detailed_case).delete()
        Comment.objects.filter(base_case=detailed_case).delete()
    DetailedCase.objects.all().delete()

    reader: Any = csv.DictReader(io.StringIO(csv_data))
    for row in reader:
        if row["Enforcement body"] == "":
            continue
        create_detailed_case_from_dict(
            row=row, default_user=default_user, auditors=auditors, sectors=sectors
        )


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
    try:
        comment_fullname_to_user: dict[str, User] = {
            comment_fullname: User.objects.get(username=username)
            for comment_fullname, username in COMMENT_FULLNAME_TO_USERNAME.items()
        }
    except User.DoesNotExist:  # Automated tests
        logger.warning("One or more historic Users missing")
        return
    katherine: User = comment_fullname_to_user["katherine.badger"]
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
                            row["comment_fullname"], katherine
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
            created_by=katherine,
        )
