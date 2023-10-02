from typing import NewType  # noqa: D100

SelectionStatusType = NewType("SelectionStatusType", str)


class SelectionStatus:  # noqa: D101
    PASSED_TEST = SelectionStatusType("Passed Test (Awaiting)")
    DRAWN = SelectionStatusType("Drawn")
    INTERVIEW = SelectionStatusType("Awaiting Interview")
    SELECTED = SelectionStatusType("Need payment proof")
    TO_BE_ACCEPTED = SelectionStatusType("Reviewing documents")
    ACCEPTED = SelectionStatusType("Accepted")
    REJECTED = SelectionStatusType("Rejected")
    NOT_SELECTED = SelectionStatusType("Not Selected")

    SELECTION_AWAITING_STATUS = [PASSED_TEST, DRAWN]  # noqa: RUF012
    # REJECTED is on this list (which refers to candidates who are or have been SELECTED)
    # because to be in status REJECTED, the candidate was previously SELECTED
    SELECTION_POSITIVE_STATUS = [SELECTED, TO_BE_ACCEPTED, ACCEPTED, REJECTED]  # noqa: RUF012
    SELECTION_NEGATIVE_STATUS = [NOT_SELECTED]  # noqa: RUF012

    FINAL_STATUS = [ACCEPTED, REJECTED, NOT_SELECTED]  # noqa: RUF012
