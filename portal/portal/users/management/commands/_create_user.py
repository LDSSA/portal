import uuid

from allauth.account.models import EmailAddress

from portal.users.models import User


def add_user_options(parser) -> None:
    parser.add_argument("-u", "--username", type=str, required=True)
    parser.add_argument("-p", "--password", type=str, required=True)
    parser.add_argument("-e", "--email", type=str, required=True)
    parser.add_argument("-n", "--name", type=str, required=True)
    parser.add_argument("-git", "--github", type=str, required=True)
    parser.add_argument("-s", "--slack", type=str, required=True)
    parser.add_argument(
        "-g", "--gender", type=str, choices=["female", "male"], required=True
    )
    parser.add_argument(
        "-t",
        "--ticket",
        type=str,
        choices=["regular", "student", "company", "scholarship"],
        default="regular",
    )


def create_user(
    username,
    password,
    email,
    name,
    github,
    slack,
    gender,
    ticket,
    user_type="student",
    **kwargs,
) -> User:
    if user_type == "student":
        is_student = True
        is_instructor = False
    elif user_type == "instructor":
        is_student = False
        is_instructor = True
    else:
        is_student = False
        is_instructor = False

    user = User(
        username=username,
        email=email,
        name=name,
        github_username=github,
        slack_member_id=slack,
        is_student=is_student,
        is_instructor=is_instructor,
        deploy_private_key=uuid.uuid4(),
        deploy_public_key=uuid.uuid4(),
        code_of_conduct_accepted=True,
        gender=gender,
        ticket_type=ticket,
        is_active=True,
    )
    user.set_password(password)
    user.save()

    EmailAddress.objects.get_or_create(
        user=user,
        email__iexact=email,
        verified=True,
        defaults={"email": email},
    )
    return user
