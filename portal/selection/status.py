from typing import NewType

SelectionStatusType = NewType("SelectionStatusType", str)


class SelectionStatus:
    PASSED_TEST = SelectionStatusType("Passed Test (Awaiting)")
    DRAWN = SelectionStatusType("Drawn")
    INTERVIEW = SelectionStatusType("Awaiting Interview")
    SELECTED = SelectionStatusType("Need payment proof")
    TO_BE_ACCEPTED = SelectionStatusType("Reviewing documents")
    ACCEPTED = SelectionStatusType("Accepted")
    REJECTED = SelectionStatusType("Rejected")
    NOT_SELECTED = SelectionStatusType("Not Selected")

    SELECTION_AWAITING_STATUS = [PASSED_TEST, DRAWN]
    # REJECTED is on this list (which refers to candidates who are or have been SELECTED)
    # because to be in status REJECTED, the candidate was previously SELECTED
    SELECTION_POSITIVE_STATUS = [SELECTED, TO_BE_ACCEPTED, ACCEPTED, REJECTED]
    SELECTION_NEGATIVE_STATUS = [NOT_SELECTED]

    FINAL_STATUS = [ACCEPTED, REJECTED, NOT_SELECTED]
