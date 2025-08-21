from maid.flows.get_student_housing_aarhus import check_whats_up
from os import getenv
from dotenv import load_dotenv

load_dotenv()

for _ in (getenv("FLOWS") or '').split():
    match _:
        case '0':
            check_whats_up()
