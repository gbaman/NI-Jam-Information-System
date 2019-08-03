import requests
from bs4 import BeautifulSoup


def check_dbs_certificate(certificate_number, applicant_surname, applicant_dob, verifier_forename, verifier_surname, organisation_name):
    params = {"dateOfBirth": applicant_dob.strftime("%d/%m/%Y"), "surname": applicant_surname, "organisationName": f"{organisation_name} - API", "employeeForename": verifier_forename, "employeeSurname": verifier_surname, "hasAgreedTermsAndConditions": "true"}
    r = requests.get(f"https://secure.crbonline.gov.uk/crsc/api/status/{certificate_number}", params=params)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, features="html.parser")
        status = soup.find("status").string
        if status == "NO_MATCH_FOUND" or status == "NEW_INFO":
            return False
        elif status == "NON_BLANK_NO_NEW_INFO" or "BLANK_NO_NEW_INFO":
            return True
    return False
