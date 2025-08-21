from dotenv import load_dotenv
from maid.flows.get_student_housing_aarhus import check_whats_up
from os import getenv

for _ in (getenv("FLOWS") or '').split():
    match _:
        case '0':
            check_whats_up()
